# Progress

Updated at the end of every Claude Code session (see [CLAUDE.md](https://github.com/StardustModulator/benchtop-lab/blob/main/CLAUDE.md)). Newest session log entry first.
Times are IST (Asia/Kolkata, UTC+5:30).

## Status

| | |
| --- | --- |
| Phase | 3: build in progress |
| Current milestone | M0 Foundations |
| Next session | **S03 · Compat layer v0 and `benchtop doctor`** |
| Sessions done | 2 / 70 (+ 0 contingency used of ~7) |
| Percent complete | 2.9% |
| Estimated sessions remaining | 68 |
| Estimated nights remaining | ~11 (68 sessions ÷ ~6 per night on the 23:00–07:00 IST schedule; range 8–14 incl. contingency) |
| Last green `main` commit | S02 merge, PR #2 (see session log) |

## Milestones

| Milestone | Sessions | Done | Status |
| --- | --- | --- | --- |
| M0 Foundations | S01–S04 | 2/4 | in progress |
| M1 Sim core | S05–S09 | 0/5 | not started |
| M2 Task suite | S10–S16 | 0/7 | not started |
| M3 Experts and demos | S17–S22 | 0/6 | not started |
| M4 Grader | S23–S30 | 0/8 | not started |
| M5 Dataset doctor | S31–S35 | 0/5 | not started |
| M6 Reference baselines | S36–S40 | 0/5 | not started |
| M7 Projects P0–P4 | S41–S50 | 0/10 | not started |
| M8 Projects P5–P7 | S51–S57 | 0/7 | not started |
| M9 Hardware path | S58–S62 | 0/5 | not started |
| M10 Hardening and v1.0 | S63–S70 | 0/8 | not started |

## Blockers and decisions waiting on Shiva

| ID | Item | Needed by |
| --- | --- | --- |
| D1 | Confirm the name "Benchtop Lab" (renaming later is cheap until S04, costly after) | S04 |
| D7 | Allow branch protection on `main` (no force-push, require the **CI passed** check) and drop the unused `delete_repo` scope from the build machine's GitHub login. **Still pending after S02**: not applied without approval; the exact command is in the S02 log entry | now |
| D8 | Enable GitHub Discussions (PLAN §16 uses it for Q&A, show-and-tell and RFCs); until then proposals use the Task proposal issue form | S41 |
| D2 | Free Kaggle account for GPU reference runs (optional) | S40 |
| D3 | Hugging Face account/org for EnvHub Spaces, datasets, checkpoints (optional) | S36 |
| D4 | PyPI account for Trusted Publishing of `benchtop-lab` (optional) | S70 |
| D5 | Access to a real SO-101 (optional) | S62 |
| D6 | Contact email for conduct/security reports (optional) | S70 |

## Ideas and follow-ups (not in the current plan)

- S04 `tools/bump_version.py`: pin inter-package dependencies as `==<shared version>` so PyPI installs keep the
  six packages in lockstep (today they depend on each other unpinned; the workspace keeps them aligned locally).
- README still carries the "Status: planning" badge and note; refresh it when the docs site lands (S04).
- Remove the `|| [ $$? -eq 5 ]` guards from `make test-slow` / `test-render` once tests with those markers exist
  (S05 for render, S03 or S05 for slow), so an accidentally empty suite fails again.
- Freeze pre-commit hook revisions to commit SHAs (`pre-commit autoupdate --freeze`) so local hooks match the
  SHA-pinning rule used for workflows; it also bumps versions, so do it as its own small change.
- Nightly: add an issue-on-failure or badge check once there is something long-running to watch (S09 onwards).
- If a second `conftest.py` is ever needed, switch mypy to `explicit_package_bases` (test file names must be unique
  today; enforced by `tests/test_repo_tooling.py`).

## Session log

<!--
Template for each entry (newest first):

### SNN · <title> — <DONE | PARTIAL | BLOCKED>
- Date (IST): YYYY-MM-DD HH:MM–HH:MM
- Branch / PR: session/SNN-slug → merged to main in <sha> | PR #<n> (tests failing: <why>)
- Done:
  - ...
- Tests: <passed>/<total>, coverage <x>%, `ruff`/`mypy` clean
- Next: SNN+1 <title> (or: resume SNN at task <k>)
- Blockers: none | <what, who can unblock>
- Notes for next session: <context that would otherwise be lost>
- Usage: stopped early due to usage limit? yes/no
-->

### S02 · Continuous integration and repo hygiene — DONE
- Date (IST): 2026-11-23 17:56–18:09
- Branch / PR: `session/S02-ci-repo-hygiene` → PR #2, rebase-merged by `land-pr.sh` after green CI (ADR-008).
- Done:
  - `.github/workflows/ci.yml` on every pull request and push to `main`: `lint` (ruff, ruff format, import-linter,
    file-hygiene hooks, actionlint), `typecheck` (mypy strict), `test` (ubuntu-latest, Python 3.12 and 3.13, 85%
    coverage gate), `slow`, `render` (`MUJOCO_GL=egl`; apt `libegl1 libegl-mesa0 libgl1-mesa-dri libosmesa6`
    verified to install on ubuntu-latest), `reuse` (isolated `uvx`, ADR-010), `gitleaks` (release binary 8.30.1
    verified by SHA-256, scans the full history, `--redact`), and `ci-ok` ("CI passed"): one always-running summary
    check meant to be the single required status for branch protection.
  - `.github/actions/setup`: shared composite action (uv 0.13.8 pinned, uv cache keyed on `uv.lock`,
    `uv sync --locked --all-packages --all-groups --extra cpu`; `torch: none` for the lint job).
  - `.github/workflows/nightly.yml` skeleton: 02:00 IST schedule + manual start, ubuntu-latest and macos-latest ×
    Python 3.12/3.13, fast + slow suites. It also runs on pull requests that change it or the setup action, which
    is how the macOS legs were proven green on PR #2.
  - Every action pinned to a full commit SHA with a `# vX.Y.Z` comment (checkout v7.0.1, setup-uv v10.4.0, cache
    v6.1.0); top-level `permissions: contents: read`; `persist-credentials: false`; no secrets; job timeouts;
    no `${{ }}` inside `run:` scripts. `tests/test_ci_config.py` enforces all of it.
  - Issue forms (bug, task proposal, lesson feedback) with blank issues off and a private-security-report link;
    `PULL_REQUEST_TEMPLATE.md`; `CODEOWNERS`; `dependabot.yml` (weekly grouped PRs for GitHub Actions, including the
    composite action directory, and for uv); `SECURITY.md` (GitHub private vulnerability reporting, scope, targets).
  - `actionlint` v1.7.12 pre-commit hook (uses shellcheck when installed). Makefile: new `test-slow`,
    `test-render`, `hooks`; CI calls the Makefile targets, so the Makefile is now executed on every run.
  - README: CI and Nightly badges. CONTRIBUTING: CI section, security row, task proposals via the issue form.
- Repository setting changed: **private vulnerability reporting enabled** via `gh api -X PUT
  repos/StardustModulator/benchtop-lab/private-vulnerability-reporting` (SECURITY.md depends on it; undo with
  `-X DELETE`). Nothing else on the repository was changed.
- Branch protection (D7): **pending, not applied** (no recorded owner approval). After approval run:
  `gh api -X PUT repos/StardustModulator/benchtop-lab/branches/main/protection --input -` with
  `{"required_status_checks":{"strict":true,"contexts":["CI passed"]},"enforce_admins":false,
  "required_pull_request_reviews":null,"restrictions":null,"allow_force_pushes":false,"allow_deletions":false,
  "required_linear_history":true}`.
- Dependencies added (dev group only, permissive): `pyyaml` (MIT; was already locked through pre-commit) and
  `types-pyyaml` (Apache-2.0) for the workflow tests.
- Tests: 133/133 passed, coverage 98.6%; slow 0/0 and render 0/0 (none exist yet); ruff, ruff format, mypy --strict,
  lint-imports (4/4 kept), pre-commit (all hooks incl. actionlint), reuse lint clean. CI on PR #2: all 13 checks
  green (9 from `ci.yml`, 4 nightly-matrix legs incl. macOS arm64 with `torch==2.15.0+cpu` on both Pythons).
  `ubuntu-latest` currently resolves to Ubuntu 26.04.
- Reviewer: CHANGES REQUIRED on the first pass (PR template allowed small binaries; CONTRIBUTING/SECURITY overstated
  enforcement and still pointed at Discussions; test gaps: secrets spelling, composite script never executed,
  concurrency, uv version drift, issue-form schema); all fixed, plus the nits except hook-rev freezing (follow-up).
- Next: S03 Compat layer v0 and `benchtop doctor`.
- Blockers: none. D7 still waits on the owner; D8 (enable Discussions) is new and not urgent.
- Notes for next session:
  - Merge with `/workspace/projects/benchtop-lab-runner/land-pr.sh` (not `gh pr merge`). Open the PR early as a
    draft to get CI feedback, mark it ready (`gh pr ready`) before landing; the script refuses drafts.
  - CI installs torch through `--extra cpu`; the local gate does not. When S03 adds `lerobot`, make sure the
    locked sync still works on Python 3.13 and on macOS arm64 (the nightly matrix runs on PRs that touch
    `nightly.yml` or the setup action; touch one of them in S03 to prove it, or start the workflow by hand).
  - `make test-slow` / `make test-render` accept pytest's exit code 5 (no tests collected). Drop that guard in the
    session that adds the first test with the marker.
  - New workflow files must satisfy `tests/test_ci_config.py`; a new job in `ci.yml` must be added to `ci-ok.needs`
    and to the expected job set in the test.
  - Dependabot will open grouped PRs on Mondays; they are the owner's to merge (or a session may fold them in).
- Usage: stopped early due to usage limit? no

### S01 · Monorepo skeleton and quality tooling — DONE
- Date (IST): 2026-11-23 17:05–18:00
- Branch / PR: `session/S01-monorepo-skeleton` → fast-forwarded to `main` after a green local gate (ADR-008, pre-CI).
- Done:
  - uv workspace (Python 3.12, `.python-version`, `uv.lock`) with six src-layout hatchling packages
    (`benchtop-core`, `-sim`, `-grade`, `-data`, `-real`, `-lab`), each with `py.typed`, `__version__ = "0.1.0.dev0"`
    (hatch reads it), README and a copy of LICENSE (symlinks broke `uv build`; regression test added).
  - `benchtop` CLI (Typer) with `--version`/`-V` and `python -m benchtop_lab`; semantic Rich theme in
    `benchtop_lab.console`. One pure `colour_settings()` drives both our consoles and Typer's help screens:
    `NO_COLOR` → zero ANSI codes, `FORCE_COLOR=0` → off (Rich/Typer alone treat it as "on" and Typer forces colour
    on `GITHUB_ACTIONS`), pipes → plain text.
  - ruff (lint + format, 110), mypy strict over src and tests, pytest (5 markers deselected by default,
    `--strict-markers`, warnings as errors, importlib mode), coverage (branch, ≥ 85%).
  - import-linter: layers (CLI → grade | data | real → core | sim), `sim-standalone`, `data-core-only`, and the
    lerobot/torch boundary (only `benchtop_core.compat` / `.policies`), `include_external_packages = true`.
    Manually verified that each contract BREAKS on an injected violation.
  - torch `cpu`/`cu` extras on `benchtop-core`, declared conflicting, mapped to explicit PyTorch indexes (cpu, cu126).
  - `.pre-commit-config.yaml`: pre-commit-hooks v6.0.0 (EOF, whitespace, large files 1 MB, merge conflicts, toml,
    yaml, json, LF), ruff v0.17.6, local `uv run mypy` and `uv run lint-imports`, reuse v6.3.0, gitleaks v8.30.1.
    Licence texts are excluded from fixers (the EOF fixer had touched LICENSE-CONTENT; reverted, never committed).
  - `REUSE.toml` + `LICENSES/` (Apache-2.0, CC-BY-4.0): `reuse lint` compliant. `Makefile` (setup, lint, format,
    type, test, test-all, reuse, docs, gate). ADR-004 accepted; ADR-010 added (copyleft dev tools such as REUSE run
    only as isolated CLIs, never in `uv.lock`). ARCHITECTURE §2 now states grade/data/real are independent siblings.
- Dependencies added (all permissive): runtime `typer` 0.29 (MIT), `rich` 15.0 (MIT) and their deps `click` (BSD-3),
  `shellingham` (ISC), `typing-extensions` (PSF), `annotated-doc` (MIT), `pydantic`/`pydantic-core`/`annotated-types` (MIT), `typing-inspection` (MIT), `pygments` (BSD-2), `markdown-it-py`/`mdurl` (MIT); dev group
  `ruff` (MIT), `mypy` (MIT), `pytest`, `pytest-cov`, `pytest-xdist` (MIT), `hypothesis` (MPL-2.0),
  `import-linter`/`grimp` (BSD-2), `pre-commit` (MIT); optional extra `torch` (BSD-3). REUSE (GPL-3.0+) is a
  pre-commit/uvx tool only (ADR-010).
- Tests: 69/69 passed, coverage 98.6%; slow 0/0 and render 0/0 (none exist yet; pytest exits 5 "no tests
  collected"); ruff, ruff format, mypy --strict, lint-imports (4/4 kept), pre-commit (all hooks), reuse lint clean.
  Also verified from a fresh clone: `uv sync --all-packages --all-groups && uv run benchtop --version`.
- Reviewer: CHANGES REQUIRED on the first pass (CLI tests depended on the machine's `NO_COLOR`; Typer help ignored
  the colour policy; PROGRESS missing; private Rich API; dark-theme-unreadable blue accent; cu128 lagging; mypy
  duplicate-module risk); all fixed in this session.
- Next: S02 Continuous integration and repo hygiene (first session using the PR merge flow).
- Blockers: none. D7 (branch protection) is needed by S02.
- Notes for next session:
  - The build machine sets `NO_COLOR=1`, `FORCE_COLOR=0` and `TERM=dumb` globally. CLI tests neutralise these via
    `packages/benchtop-lab/tests/conftest.py`; keep that pattern for every new CLI test.
  - CI: run `reuse` as `uvx --from 'reuse[charset-normalizer]==6.3.0' reuse lint` (it needs an encoding module).
    gitleaks's pre-commit hook builds with Go. `make` is not installed on the build machine.
  - `pytest -m slow` / `-m render` exit 5 until tests with those markers exist; the CI jobs must treat 5 as success
    or add a placeholder test (the Makefile already treats 5 as success).
  - torch: CPU index resolves 2.15.0, cu126 resolves 2.14.1. S03 must pin one torch range compatible with LeRobot 0.7
    for both flavours. Switch import-linter `unmatched_ignore_imports_alerting` to "warn" once compat imports lerobot.
  - Reviewer follow-up for S03: under `NO_COLOR`, `colour_settings` returns `force_terminal=False`, which also
    disables Rich live displays/spinners on a real terminal. If `benchtop doctor` wants a spinner, return
    `force_terminal=None` there (`color_system=None` already strips styles) and update the docstring.
  - Python 3.12 is installed through uv (`uv python install 3.12`); system Python is 3.13.
- Usage: stopped early due to usage limit? no

### Owner rule · UI excellence — DONE
- Date (IST): 2026-11-23
- Done: standing rule that every UI is world-class, top-university-lab quality. Added the "UI excellence" section to
  CLAUDE.md, the `ui-excellence` skill (fonts, type scale, measured WCAG AA colour tokens for light/dark, chart
  palette, surface guidance, verification steps, review checklist), and UI checks in `reviewer`,
  `curriculum-reviewer` and `/session`.
- Next: S01 Monorepo skeleton and quality tooling.
- Blockers: none.

### Phase 2 · Planning — DONE
- Date (IST): 2026-11-23
- Done: research, PLAN.md, ARCHITECTURE.md, MILESTONES.md, CLAUDE.md, `.claude/` agents/commands/skills, licenses,
  community files.
- Next: S01 Monorepo skeleton and quality tooling.
- Blockers: none.
