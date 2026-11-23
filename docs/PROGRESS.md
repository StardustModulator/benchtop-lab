# Progress

Updated at the end of every Claude Code session (see [CLAUDE.md](https://github.com/StardustModulator/benchtop-lab/blob/main/CLAUDE.md)). Newest session log entry first.
Times are IST (Asia/Kolkata, UTC+5:30).

## Status

| | |
| --- | --- |
| Phase | 3: build in progress |
| Current milestone | M0 Foundations |
| Next session | **S02 · Continuous integration and repo hygiene** |
| Sessions done | 1 / 70 (+ 0 contingency used of ~7) |
| Percent complete | 1.4% |
| Estimated sessions remaining | 69 |
| Estimated days remaining | ~28 (69 sessions ÷ 2.5/day; ~30 with the ~7 contingency sessions) |
| Last green `main` commit | S01 merge (see session log) |

## Milestones

| Milestone | Sessions | Done | Status |
| --- | --- | --- | --- |
| M0 Foundations | S01–S04 | 1/4 | in progress |
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
| D7 | Allow branch protection on `main` (no force-push, require CI) and drop the unused `delete_repo` scope from the build machine's GitHub login | S02 |
| D2 | Free Kaggle account for GPU reference runs (optional) | S40 |
| D3 | Hugging Face account/org for EnvHub Spaces, datasets, checkpoints (optional) | S36 |
| D4 | PyPI account for Trusted Publishing of `benchtop-lab` (optional) | S70 |
| D5 | Access to a real SO-101 (optional) | S62 |
| D6 | Contact email for conduct/security reports (optional) | S70 |

## Ideas and follow-ups (not in the current plan)

- S04 `tools/bump_version.py`: pin inter-package dependencies as `==<shared version>` so PyPI installs keep the
  six packages in lockstep (today they depend on each other unpinned; the workspace keeps them aligned locally).
- S02: install `make` on the CI image (and note it in CONTRIBUTING) — the build machine has none, so the Makefile
  has not been executed yet; only its targets are checked by a test.
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
  `shellingham` (ISC), `typing-extensions` (PSF), `pygments` (BSD-2), `markdown-it-py`/`mdurl` (MIT); dev group
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
