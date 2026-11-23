# CLAUDE.md: rules for Claude Code in this repository

You are building **Benchtop Lab**: a free, open-source monorepo of graded, sim-first robot-learning projects for the
SO-101 arm, built on LeRobot 0.7 and MuJoCo. Quality over speed. Never rush; never cut corners to "finish" a session.

Read these before doing anything (only the parts you need; see "Working efficiently"):
1. `docs/PROGRESS.md`: the status table, blockers and the latest session-log entry with its notes for next session.
2. `docs/MILESTONES.md`: your session's section only (goal, tasks, acceptance, tests).
3. `docs/PLAN.md` and `docs/ARCHITECTURE.md`: the sections your session cites or touches. Follow the spec. If the
   spec is wrong, record an ADR in `docs/DECISIONS.md` and explain the change; do not silently diverge.

## Session protocol (one headless run = one session)

1. `git checkout main && git pull --ff-only`. Confirm the working tree is clean.
2. Identify the next session `SNN` from PROGRESS.md. If PROGRESS.md says to resume a partial session, resume it.
3. Create a branch: `git checkout -b session/SNN-<short-slug>`.
   If a `session/SNN-*` branch already exists on origin (a previous run was cut off), check it out and resume from
   its last commit and the PARTIAL notes instead of starting over.
4. Plan briefly (a todo list), then implement only that session's tasks. Out-of-scope ideas go to PROGRESS.md
   "Ideas and follow-ups". Commit and push the branch after each completed task, so an interrupted run loses little.
5. Write tests alongside code. Run the full gate (below). Fix failures. Use the `test-runner` subagent for long runs and
   the `reviewer` subagent on your diff before finishing.
6. Update `docs/PROGRESS.md` (status table, milestone table, a new session-log entry at the top of the log) and,
   if you changed a design decision, `docs/DECISIONS.md`.
7. Commit with Conventional Commits (`feat(sim): add reach task`, `test(grade): ...`, `docs: ...`). Small, logical commits.
8. **Merge flow (ADR-008).** Rebase the branch on `main` and push it.
   - Before CI exists (S01 only): if the local gate is green, `git checkout main && git merge --ff-only <branch>` and
     `git push origin main`.
   - From S02 on: open a PR (`gh pr create --fill --base main`), wait for CI (`gh pr checks --watch`), and if every
     check is green, merge with `gh pr merge --rebase --delete-branch`.
   - **If anything is red** that you cannot fix in this session: convert the PR to draft (`gh pr ready --undo`) or
     open it with `--draft`, describe what fails and why, record a blocker in PROGRESS.md, and stop.
   - Never push a failing build to `main`. Never use `--no-verify`. Never force-push anything to `main`.
     (Only the build runner, outside this repo, may save an emergency WIP checkpoint with hooks skipped when a run
     is cut off, on the `session/*` branch only and after its secret scan and gitleaks pass. When you resume a
     branch whose tip is such a `wip(...) (hooks skipped)` commit, fix what the hooks report before anything else.
     Those commits never merge until the hooks, the full gate and CI are green.)
9. Finish by printing a short summary: session id, DONE/PARTIAL/BLOCKED, commit SHA or PR URL, tests passed, next session.

## Usage limits

- Headless runs may be cut off without warning (usage limit or the runner's wall-clock cap). That is why you commit
  and push the session branch after every completed task, and keep a running "Notes for next session" in the
  PROGRESS.md entry on the branch as you go.
- If you see a usage-limit warning, stop starting new work: commit what is green on the branch, finish the PARTIAL
  entry in PROGRESS.md saying exactly which task to resume from, push the branch, and end.
- Do not loop on retries. If the same failure persists after two genuine fix attempts, record it as a blocker.
- Prefer targeted test runs while iterating (`uv run pytest packages/benchtop-sim -x -q`), full gate once at the end.

## Working efficiently (usage budget)

The Claude usage allowance, not wall-clock time, decides how many sessions finish per night. Every token you add to
the context is re-read on every later turn, so keep the context small. This changes how you work, never what you
ship: the gate, tests, review and the UI bar are unchanged.

- **Orient narrowly.** `grep -n '^#' docs/PLAN.md docs/ARCHITECTURE.md`, then `sed -n 'A,Bp'` the sections you need.
  Read your session in MILESTONES.md with `sed -n '/^### SNN /,/^### /p'` (or its table row). Read PROGRESS.md's
  status table and the newest log entry only. Never `cat` a whole planning doc, and never `cat` several files in
  one command; read at most ~200 lines at a time with the Read tool's offset/limit.
- **Third-party code** (site-packages, cloned upstream repos): `grep -rn` for the symbol, then read that range; for
  open-ended exploration ask the `Explore` subagent and keep only its summary.
- **Short command output.** Pipe long output through `| tail -n 40` or `grep`. Pytest while iterating:
  `uv run pytest <path> -q -x --no-header --tb=short 2>&1 | tail -n 40`; rerun only failing test ids.
  Use `git diff --stat` before a full diff and diff only the files you need. `uv sync -q`.
- **Edit, don't rewrite.** Use the Edit tool for changes to existing files instead of regenerating them through
  `python - <<EOF` or `cat > file`. Don't print a file you just wrote.
- **Images and the web.** Inspect a rendered screenshot once, at ≤ 800 px wide, and only when checking a UI. Use the
  `web-fetch` subagent for documentation pages (it returns a summary) rather than WebFetch in the main context.
- **Gate through the subagent.** Iterate with targeted tests; run the full gate once via `test-runner` before review
  and once after fixes. Run `uv run ruff check --fix . && uv run ruff format .` before every commit so hooks pass.
- **One review pass.** Call `reviewer` once on the final diff (milestone-final sessions: one combined pass over the
  milestone). Fix every Must fix and re-run the gate; call `reviewer` again only if a fix changed the design.
- **Resume cheaply.** On an existing branch: `git log --oneline main..HEAD`, `git diff main...HEAD --stat` and the
  PARTIAL notes. Don't re-read files you won't change.

## The gate (all must pass before merging to main)

```bash
uv sync --all-packages --all-groups
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run lint-imports
uv run pytest -q --cov --cov-fail-under=85   # default markers exclude slow, render, network, gpu, hardware
MUJOCO_GL=egl uv run pytest -q -m "render"   # when the session touched sim rendering, video or reports
uv run pytest -q -m "slow"                   # when the session touched sim, grader, compat or datasets
uv run mkdocs build --strict      # when the session touched docs or docstrings (after S04)
```

Until S01 creates these tools, the gate is "the repository is consistent and docs render".

## Hard rules

- **Never commit secrets** (tokens, keys, `.env`, HF/PyPI credentials, `~/.cache/huggingface/token`). Read tokens only
  from the environment. gitleaks runs in pre-commit and CI; if it flags something, remove it, do not allowlist it.
- **Never publish or post**: no PyPI uploads, no Hugging Face pushes, no git tags or GitHub releases, no
  Discord/X/Reddit/HN posts, no emails, no issues or PRs on other repositories (upstream fixes are drafted as patches
  for the owner). Launch material is written as drafts in `docs/launch/drafts/` only. Publishing happens
  only after the owner explicitly approves it, recorded in PROGRESS.md.
- **Never spend money** or sign up for services.
- **Never add a paid tier**, license key, telemetry or tracking. This project is free forever (ADR-001).
- **Licensing**: code Apache-2.0, content CC BY 4.0. Add SPDX headers to new files. Only add dependencies with
  permissive or weak-copyleft licenses (Apache-2.0, MIT, BSD, ISC, PSF, MPL-2.0). Never add GPL/AGPL dependencies,
  and never vendor binaries. Never copy code from sources with
  incompatible or unknown licenses. Vendored assets keep their upstream LICENSE and are listed in NOTICE.
- **LeRobot boundary**: only `benchtop_core.compat` and the `benchtop_core.policies` plugin (ADR-007) import `lerobot`
  or `torch`. `benchtop_sim` never imports `lerobot`, `torch`, or other `benchtop_*` packages.
- **Do not modify** `LICENSE`, `LICENSE-CONTENT`, `CODE_OF_CONDUCT.md`, or accepted ADRs.
- **Hardware safety**: code that can move a real arm must default to read-only and require `--allow-motion`.
  Hardware tests use mocks; real-device tests carry the `hardware` marker and never run in CI.

## SO-101 conventions (do not deviate)

- Joints, in order: `shoulder_pan, shoulder_lift, elbow_flex, wrist_flex, wrist_roll, gripper`; names `<joint>.pos`.
- Units: degrees for arm joints ("new calibration", zero at mid-range); gripper 0 = closed, 100 = open.
- Control: absolute joint position targets at 30 fps. Cameras `front` and `wrist`.
- `LEROBOT_SIM = {"fps": 30, "control_mode": "position", "semantics": "so101-joint-degrees-v1", "state_names": JOINT_NAMES, "action_names": JOINT_NAMES, "robot_type": "so_follower"}`.
- Episodes terminate on the first step where the full success condition holds; `is_success` is reported every step.
- Observations: `pixels` (dict of HWC uint8), `agent_pos` (float32[6]), optional `environment_state` (float32).

## Code style

- Python 3.12, type hints everywhere, `mypy --strict` clean. Prefer dataclasses/Pydantic v2 models over dicts.
- ruff formatting, line length 110. Google-style docstrings on public APIs (rendered by mkdocstrings).
- Pure functions for checks and statistics; side effects at the edges (CLI, I/O).
- No global RNG. Every random draw comes from a `numpy.random.Generator` derived from an explicit seed.
- Errors for users say what happened, the likely cause and the next command to run.
- Keep modules small and cohesive; no file over ~400 lines without a reason.
- No new top-level dependencies without noting them (and their license) in the session log.

## Tests

- pytest; tests live in `packages/<pkg>/tests/` and cross-package tests in `tests/`.
- Markers: `slow` (> 5 s or uses LeRobot training/eval), `render` (needs offscreen GL), `network`, `gpu`, `hardware`.
  The default `addopts` deselects all five; CI runs `slow` and `render` in separate jobs.
- Unit tests never touch the network; mock Hub access.
- Every success check needs positive **and** adversarial tests. Every bug fix gets a regression test.
- Headless rendering: `MUJOCO_GL=egl` (fallback `osmesa`).
- Coverage target ≥ 85% for `benchtop_*` packages excluding hardware I/O.

## UI excellence (standing owner rule)

Every interface in this repo (MkDocs site, grader report cards and other HTML reports, dataset-doctor output,
dashboards, the landing page, charts and figures, and rich CLI output) must be **world-class, top-university-lab
quality**: think MIT CSAIL / Stanford AI Lab project pages and Distill.pub, with Linear/Vercel-level polish.

- Before building or changing any UI, load the **`ui-excellence`** skill (`.claude/skills/ui-excellence/SKILL.md`)
  and use its design tokens (font pairing Inter + Source Serif 4 + JetBrains Mono, self-hosted; 1.25 type scale;
  60–75ch prose measure; measured colour tokens with a first-class dark mode; Okabe–Ito chart palette).
- Accessibility is WCAG 2.2 AA in both themes, responsive down to 320 px, keyboard navigable, no colour-only status.
- No CDN fonts, analytics, trackers or cookies (ADR-001). OFL-1.1 is allowed for vendored font files only.
- Verify, don't assume: render it, screenshot light/dark at mobile and desktop widths, run an a11y check when the
  tooling exists, and add tests (contrast of tokens, required report sections, `NO_COLOR` output).
- The `reviewer` agent applies the skill's checklist to every UI diff; a UI that would not hold up next to a
  Distill.pub article is "Must fix", not a nit.

## Docs and lessons

- Lessons are Markdown under `projects/pN_*/lesson/` and appear on the MkDocs site. Write plainly, define every term on
  first use, include predict → run → explain blocks, and show real commands that were actually run.
- Every number in a lesson must come from a real run recorded in the repo (results.json) or be marked provisional.

## Useful commands

```bash
uv run benchtop --help
uv run benchtop doctor
uv run pytest packages/benchtop-sim -x -q
MUJOCO_GL=egl uv run pytest -m render -q
uv run mkdocs serve
```

## Repository map

See `docs/PLAN.md` §10. Planning docs live in `docs/`; project content in `projects/`; packages in `packages/`.
Claude Code helpers: `.claude/commands/session.md` (`/session`), `.claude/agents/` (`test-runner`, `reviewer`,
`curriculum-reviewer`), `.claude/skills/` (LeRobot compat, MuJoCo env authoring, lesson writing, UI excellence).
