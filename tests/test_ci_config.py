# SPDX-FileCopyrightText: 2026 Benchtop Lab contributors
# SPDX-License-Identifier: Apache-2.0
"""CI and repository-hygiene invariants: pinned actions, least privilege, gate jobs, community files."""

import os
import re
import shutil
import subprocess
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
GITHUB = ROOT / ".github"
WORKFLOWS = sorted((GITHUB / "workflows").glob("*.yml"))
ACTIONS = sorted((GITHUB / "actions").glob("*/action.yml"))
REPO = "StardustModulator/benchtop-lab"

# `uses: owner/repo[/path]@<40 hex> # vX.Y.Z` for third-party actions; `./local/path` for our own.
PINNED_USE = re.compile(r"^[\w.-]+/[\w.-]+(/[\w./-]+)?@[0-9a-f]{40}$")
USES_LINE = re.compile(r"^\s*(?:-\s+)?uses:\s*(?P<ref>\S+)(?:\s+#\s*(?P<comment>.+))?$")
VERSION_COMMENT = re.compile(r"^v\d+\.\d+\.\d+$")


def load(path: Path) -> dict[Any, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict), f"{path} is not a YAML mapping"
    return data


def triggers(workflow: dict[Any, Any]) -> dict[str, Any]:
    # YAML 1.1 reads the bare key `on` as the boolean True.
    raw = workflow.get("on", workflow.get(True))
    assert isinstance(raw, dict), "write `on:` as a mapping of events"
    return raw


def steps_of(document: dict[Any, Any]) -> Iterator[tuple[str, dict[str, Any]]]:
    """Yield (job name, step) for a workflow, or ("composite", step) for a composite action."""
    if "runs" in document:
        for step in document["runs"]["steps"]:
            yield "composite", step
    for job_id, job in document.get("jobs", {}).items():
        for step in job.get("steps", []):
            yield job_id, step


def ids(paths: list[Path]) -> list[str]:
    return [str(p.relative_to(ROOT)) for p in paths]


def test_the_expected_workflows_exist() -> None:
    assert {p.name for p in WORKFLOWS} >= {"ci.yml", "nightly.yml"}
    assert ACTIONS, "the shared setup action is missing"


def is_pinned(ref: str) -> bool:
    return ref.startswith("./") or PINNED_USE.fullmatch(ref) is not None


@pytest.mark.parametrize(
    ("ref", "pinned"),
    [
        ("actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1", True),
        ("github/codeql-action/init@3d3c42e5aac5ba805825da76410c181273ba90b1", True),
        ("./.github/actions/setup", True),
        ("actions/checkout@v7", False),
        ("actions/checkout@main", False),
        ("actions/checkout@3d3c42e", False),
        ("actions/checkout", False),
        ("docker://alpine:3.20", False),
    ],
)
def test_pin_check_accepts_only_full_shas_and_local_actions(ref: str, pinned: bool) -> None:
    assert is_pinned(ref) is pinned


@pytest.mark.parametrize("path", WORKFLOWS + ACTIONS, ids=ids(WORKFLOWS + ACTIONS))
def test_every_action_is_pinned_to_a_full_commit_sha_with_a_version_comment(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    seen = 0
    for number, line in enumerate(text.splitlines(), start=1):
        if "uses:" not in line or line.lstrip().startswith("#"):
            continue
        match = USES_LINE.match(line)
        assert match, f"{path.name}:{number}: cannot parse `{line.strip()}`"
        ref, comment = match["ref"], match["comment"]
        seen += 1
        assert is_pinned(ref), f"{path.name}:{number}: pin `{ref}` to a 40-character commit SHA"
        if not ref.startswith("./"):
            assert comment, f"{path.name}:{number}: add the release as a comment, e.g. `# v1.2.3`"
            assert VERSION_COMMENT.match(comment), f"{path.name}:{number}: `{comment}` is not `vX.Y.Z`"
    # Guard against the line scan silently missing a `uses:` written in another YAML style.
    assert seen == sum(1 for _, step in steps_of(load(path)) if "uses" in step)


@pytest.mark.parametrize("path", WORKFLOWS, ids=ids(WORKFLOWS))
def test_workflow_token_is_read_only_by_default(path: Path) -> None:
    workflow = load(path)
    assert workflow.get("permissions") == {"contents": "read"}, (
        "set top-level `permissions: {contents: read}`"
    )
    for job_id, job in workflow["jobs"].items():
        extra = job.get("permissions", {})
        assert isinstance(extra, dict), f"{job_id}: spell permissions out, never `write-all`"
        assert "write" not in extra.values(), f"{job_id}: no job in this repository needs a write token yet"


@pytest.mark.parametrize("path", WORKFLOWS, ids=ids(WORKFLOWS))
def test_workflow_never_runs_untrusted_code_with_secrets(path: Path) -> None:
    events = triggers(load(path))
    assert "pull_request_target" not in events
    assert "workflow_run" not in events
    text = path.read_text(encoding="utf-8")
    assert not uses_secrets(text), "CI needs no secrets (PLAN §11: no tokens in CI)"


def uses_secrets(text: str) -> bool:
    return re.search(r"\bsecrets\s*[.\[]|\bgithub\.token\b|\bGITHUB_TOKEN\b", text) is not None


@pytest.mark.parametrize(
    ("text", "found"),
    [
        ("${{ secrets.HF_TOKEN }}", True),
        ("${{ secrets['HF_TOKEN'] }}", True),
        ("${{ secrets [ 'X' ] }}", True),
        ("token: ${{ github.token }}", True),
        ("GH_TOKEN: $GITHUB_TOKEN", True),
        ("# no secrets are needed here", False),
        ("name: Secret scan (gitleaks)", False),
    ],
)
def test_secret_detection_catches_every_spelling(text: str, found: bool) -> None:
    assert uses_secrets(text) is found


@pytest.mark.parametrize("path", WORKFLOWS, ids=ids(WORKFLOWS))
def test_only_pull_request_runs_are_cancelled_by_newer_ones(path: Path) -> None:
    # Cancelling unconditionally would cancel runs on main and leave those commits without a green check.
    concurrency = load(path)["concurrency"]
    assert concurrency["cancel-in-progress"] == "${{ github.event_name == 'pull_request' }}"
    assert "github.event.pull_request.number || github.ref" in concurrency["group"]


@pytest.mark.parametrize("path", WORKFLOWS + ACTIONS, ids=ids(WORKFLOWS + ACTIONS))
def test_checkouts_do_not_leave_credentials_on_disk(path: Path) -> None:
    for job_id, step in steps_of(load(path)):
        if str(step.get("uses", "")).startswith("actions/checkout@"):
            assert step.get("with", {}).get("persist-credentials") is False, (
                f"{path.name}:{job_id}: set `persist-credentials: false` on actions/checkout"
            )


@pytest.mark.parametrize("path", WORKFLOWS + ACTIONS, ids=ids(WORKFLOWS + ACTIONS))
def test_run_steps_do_not_interpolate_expressions_into_shell(path: Path) -> None:
    # `${{ ... }}` inside `run:` is pasted into the script before the shell sees it (script injection).
    # Pass values through `env:` instead.
    for job_id, step in steps_of(load(path)):
        assert "${{" not in str(step.get("run", "")), f"{path.name}:{job_id}: move the expression to `env:`"


@pytest.mark.parametrize("path", WORKFLOWS, ids=ids(WORKFLOWS))
def test_uv_run_never_resyncs_away_the_cpu_torch_wheels(path: Path) -> None:
    # LeRobot depends on torch, so a plain `uv run` would replace the CPU wheels with PyPI's CUDA build.
    workflow = load(path)
    assert any("actions/setup" in str(step.get("uses", "")) for _, step in steps_of(workflow))
    assert workflow["env"]["UV_NO_SYNC"] == "1"


@pytest.mark.parametrize("path", WORKFLOWS, ids=ids(WORKFLOWS))
def test_every_job_has_a_timeout(path: Path) -> None:
    for job_id, job in load(path)["jobs"].items():
        assert isinstance(job.get("timeout-minutes"), int), f"{path.name}:{job_id}: add `timeout-minutes`"


class TestCiWorkflow:
    @pytest.fixture
    def ci(self) -> dict[Any, Any]:
        return load(GITHUB / "workflows" / "ci.yml")

    def test_runs_on_pull_requests_and_pushes_to_main(self, ci: dict[Any, Any]) -> None:
        events = triggers(ci)
        assert "pull_request" in events
        assert events["push"] == {"branches": ["main"]}

    def test_has_every_gate_job(self, ci: dict[Any, Any]) -> None:
        assert set(ci["jobs"]) == {
            "lint",
            "typecheck",
            "test",
            "slow",
            "render",
            "reuse",
            "gitleaks",
            "ci-ok",
        }

    def test_tests_run_on_python_312_and_313_on_ubuntu(self, ci: dict[Any, Any]) -> None:
        job = ci["jobs"]["test"]
        assert job["runs-on"] == "ubuntu-latest"
        assert job["strategy"]["matrix"]["python-version"] == ["3.12", "3.13"]
        assert job["strategy"]["fail-fast"] is False

    def test_summary_job_needs_every_other_job_and_always_runs(self, ci: dict[Any, Any]) -> None:
        summary = ci["jobs"]["ci-ok"]
        assert set(summary["needs"]) == set(ci["jobs"]) - {"ci-ok"}
        # Without `always()` a failed dependency skips this job, and a skipped required check passes.
        assert summary["if"] == "always()"

    def test_render_job_installs_offscreen_gl_and_selects_egl(self, ci: dict[Any, Any]) -> None:
        job = ci["jobs"]["render"]
        assert job["env"]["MUJOCO_GL"] == "egl"
        script = "\n".join(str(step.get("run", "")) for step in job["steps"])
        for package in ("libegl1", "libegl-mesa0", "libgl1-mesa-dri", "libosmesa6"):
            assert re.search(rf"(?<![\w-]){re.escape(package)}(?![\w-])", script), (
                f"apt package {package} missing"
            )

    def test_gitleaks_scans_the_full_history_with_a_verified_binary(self, ci: dict[Any, Any]) -> None:
        job = ci["jobs"]["gitleaks"]
        checkout = job["steps"][0]
        assert checkout["with"]["fetch-depth"] == 0
        assert re.fullmatch(r"[0-9a-f]{64}", job["env"]["GITLEAKS_SHA256"])
        script = "\n".join(str(step.get("run", "")) for step in job["steps"])
        assert "sha256sum --check" in script
        assert "--redact" in script, "never print a found secret into a public log"

    def test_gitleaks_version_matches_the_pre_commit_hook(self, ci: dict[Any, Any]) -> None:
        hooks = load(ROOT / ".pre-commit-config.yaml")["repos"]
        rev = next(r["rev"] for r in hooks if r["repo"].endswith("gitleaks/gitleaks"))
        assert rev == f"v{ci['jobs']['gitleaks']['env']['GITLEAKS_VERSION']}"

    def test_jobs_call_makefile_targets_that_exist(self, ci: dict[Any, Any]) -> None:
        makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
        called = {
            match
            for _, step in steps_of(ci)
            for match in re.findall(r"^make ([\w-]+)$", str(step.get("run", "")), flags=re.MULTILINE)
        }
        assert called == {"lint", "hooks", "type", "test", "test-slow", "test-render", "reuse"}
        for target in called:
            assert re.search(rf"^{re.escape(target)}:", makefile, flags=re.MULTILINE), f"no `{target}` target"


class TestSetupAction:
    @pytest.fixture
    def steps(self) -> list[dict[str, Any]]:
        action = load(GITHUB / "actions" / "setup" / "action.yml")
        assert action["runs"]["using"] == "composite"
        assert action["inputs"]["torch"]["default"] == "cpu"
        steps: list[dict[str, Any]] = action["runs"]["steps"]
        return steps

    def test_uv_is_pinned_and_cached_on_the_lockfile(self, steps: list[dict[str, Any]]) -> None:
        uv = next(s for s in steps if str(s.get("uses", "")).startswith("astral-sh/setup-uv@"))
        assert re.fullmatch(r"\d+\.\d+\.\d+", uv["with"]["version"])
        assert uv["with"]["enable-cache"] is True
        assert uv["with"]["cache-dependency-glob"] == "uv.lock"

    def test_other_jobs_install_the_same_uv_version(self, steps: list[dict[str, Any]]) -> None:
        # Dependabot bumps the action SHA, not the `version:` input, so the copies could drift apart.
        versions = {
            step["with"]["version"]
            for path in WORKFLOWS + ACTIONS
            for _, step in steps_of(load(path))
            if str(step.get("uses", "")).startswith("astral-sh/setup-uv@")
        }
        assert len(versions) == 1, f"pin one uv version everywhere, found {sorted(versions)}"

    @pytest.mark.parametrize(
        ("flavour", "expected"),
        [
            ("cpu", "sync --locked --all-packages --all-groups --extra cpu"),
            ("none", "sync --locked --all-packages --all-groups"),
        ],
    )
    def test_sync_is_locked_and_selects_the_torch_flavour(
        self, steps: list[dict[str, Any]], tmp_path: Path, flavour: str, expected: str
    ) -> None:
        result = run_sync_step(steps, tmp_path, flavour)
        assert result.returncode == 0, result.stderr
        assert (tmp_path / "uv-args.txt").read_text(encoding="utf-8").strip() == expected

    def test_sync_rejects_an_unknown_torch_flavour(self, steps: list[dict[str, Any]], tmp_path: Path) -> None:
        result = run_sync_step(steps, tmp_path, "cu999")
        assert result.returncode == 2
        assert "::error::Unknown torch flavour 'cu999'" in result.stdout
        assert not (tmp_path / "uv-args.txt").exists(), "uv must not run with an unknown flavour"


def run_sync_step(
    steps: list[dict[str, Any]], tmp_path: Path, flavour: str
) -> subprocess.CompletedProcess[str]:
    """Run the composite action's sync script with a stub `uv` that records its arguments."""
    script = next(str(s["run"]) for s in steps if "uv sync" in str(s.get("run", "")))
    bash = shutil.which("bash")
    assert bash, "bash is required to test the setup action"
    stub = tmp_path / "bin" / "uv"
    stub.parent.mkdir()
    stub.write_text(f'#!/bin/sh\necho "$*" > "{tmp_path / "uv-args.txt"}"\n', encoding="utf-8")
    stub.chmod(0o755)
    env = {"PATH": f"{stub.parent}{os.pathsep}{os.environ['PATH']}", "TORCH_FLAVOUR": flavour}
    # GitHub runs `shell: bash` steps as `bash --noprofile --norc -eo pipefail`.
    return subprocess.run(
        [bash, "--noprofile", "--norc", "-eo", "pipefail", "-c", script],
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )


class TestNightlyWorkflow:
    @pytest.fixture
    def nightly(self) -> dict[Any, Any]:
        return load(GITHUB / "workflows" / "nightly.yml")

    def test_is_scheduled_and_can_be_started_by_hand(self, nightly: dict[Any, Any]) -> None:
        events = triggers(nightly)
        assert re.fullmatch(r"\d+ \d+ \* \* \*", events["schedule"][0]["cron"])
        assert "workflow_dispatch" in events

    def test_matrix_covers_linux_and_macos_on_both_pythons(self, nightly: dict[Any, Any]) -> None:
        matrix = nightly["jobs"]["platform"]["strategy"]["matrix"]
        assert {"ubuntu-latest", "macos-latest"} <= set(matrix["os"])
        assert matrix["python-version"] == ["3.12", "3.13"]

    def test_scheduled_runs_stay_in_the_main_repository(self, nightly: dict[Any, Any]) -> None:
        assert f"github.repository == '{REPO}'" in nightly["jobs"]["platform"]["if"]


class TestDependabot:
    @pytest.fixture
    def updates(self) -> dict[str, dict[str, Any]]:
        config = load(GITHUB / "dependabot.yml")
        assert config["version"] == 2
        return {entry["package-ecosystem"]: entry for entry in config["updates"]}

    def test_covers_github_actions_and_uv(self, updates: dict[str, dict[str, Any]]) -> None:
        assert set(updates) == {"github-actions", "uv"}

    def test_github_actions_updates_include_local_composite_actions(
        self, updates: dict[str, dict[str, Any]]
    ) -> None:
        # Dependabot only looks in .github/workflows unless a composite action's directory is listed.
        expected = {"/"} | {f"/{p.parent.relative_to(ROOT).as_posix()}" for p in ACTIONS}
        assert set(updates["github-actions"]["directories"]) == expected

    def test_updates_are_weekly_and_bounded(self, updates: dict[str, dict[str, Any]]) -> None:
        for entry in updates.values():
            assert entry["schedule"]["interval"] == "weekly"
            assert entry["open-pull-requests-limit"] <= 5


ISSUE_FORMS = ("bug.yml", "task-proposal.yml", "lesson-feedback.yml")
# Labels that exist in the repository by default; a form naming a missing label silently drops it.
DEFAULT_LABELS = {"bug", "documentation", "enhancement", "question", "good first issue", "help wanted"}
FORM_INPUT_TYPES = {"textarea", "input", "dropdown", "checkboxes"}


@pytest.mark.parametrize("name", ISSUE_FORMS)
def test_issue_form_is_valid(name: str) -> None:
    form = load(GITHUB / "ISSUE_TEMPLATE" / name)
    assert form["name"]
    assert form["description"]
    assert set(form["labels"]) <= DEFAULT_LABELS
    body = form["body"]
    inputs = [field for field in body if field["type"] in FORM_INPUT_TYPES]
    assert inputs, "a form needs at least one input"
    assert {field["type"] for field in body} <= FORM_INPUT_TYPES | {"markdown"}
    field_ids = [field["id"] for field in inputs]
    assert len(field_ids) == len(set(field_ids)), "field ids must be unique"
    for field in inputs:
        attributes = field["attributes"]
        # GitHub drops a form that breaks its schema from the chooser without any error.
        assert re.fullmatch(r"[A-Za-z0-9_-]+", field["id"]), f"invalid field id {field['id']!r}"
        assert attributes["label"], f"{field['id']} needs a visible label"
        if field["type"] in {"dropdown", "checkboxes"}:
            assert attributes["options"], f"{field['id']} needs at least one option"
        if "render" in attributes:
            assert field["type"] == "textarea", f"{field['id']}: only a textarea may set `render`"
    assert any(field.get("validations", {}).get("required") for field in inputs), "require at least one field"


def test_issue_chooser_points_security_reports_to_private_reporting() -> None:
    config = load(GITHUB / "ISSUE_TEMPLATE" / "config.yml")
    assert config["blank_issues_enabled"] is False
    urls = [link["url"] for link in config["contact_links"]]
    assert f"https://github.com/{REPO}/security/advisories/new" in urls


def test_security_policy_uses_private_vulnerability_reporting() -> None:
    policy = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
    assert f"https://github.com/{REPO}/security/advisories/new" in policy
    assert "do not open a public issue" in policy.lower()
    # D6 is open: no contact address may be invented.
    assert not re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", policy)


def test_codeowners_assigns_everything_to_the_maintainer() -> None:
    rules = [
        line.split()
        for line in (GITHUB / "CODEOWNERS").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]
    assert ["*", "@StardustModulator"] in rules


def test_pull_request_template_has_a_checklist() -> None:
    template = (GITHUB / "PULL_REQUEST_TEMPLATE.md").read_text(encoding="utf-8")
    assert template.count("- [ ]") >= 5
    assert "make gate" in template


def test_readme_shows_ci_badges_for_main() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for workflow in ("ci.yml", "nightly.yml"):
        assert f"https://github.com/{REPO}/actions/workflows/{workflow}/badge.svg?branch=main" in readme


def test_actionlint_runs_as_a_pre_commit_hook() -> None:
    repos = load(ROOT / ".pre-commit-config.yaml")["repos"]
    actionlint = next(r for r in repos if r["repo"].endswith("rhysd/actionlint"))
    assert re.fullmatch(r"v\d+\.\d+\.\d+", actionlint["rev"])
    assert [hook["id"] for hook in actionlint["hooks"]] == ["actionlint"]
