# Benchtop Lab: Milestones and Claude Code Sessions

This is the build plan. Each **session** is one headless Claude Code run (`/session`) sized to finish comfortably
inside one Claude Max 5-hour window, using roughly half to two-thirds of the window's budget so there is room for test
fixes. Sessions run strictly in order; a session starts only when the previous one is marked done in
[PROGRESS.md](PROGRESS.md) (or explicitly skipped with a reason).

## How to read a session

- **Goal**: one sentence.
- **Tasks**: what to build. Stay inside this list; anything extra goes to PROGRESS.md "Ideas / follow-ups".
- **Acceptance**: what must be true for the session to count as done.
- **Tests**: the tests that must exist and pass.

Every session also has these implicit requirements (from [CLAUDE.md](https://github.com/StardustModulator/benchtop-lab/blob/main/CLAUDE.md)): work on a `session/SNN-<slug>`
branch; the full gate in CLAUDE.md (ruff, ruff format, mypy, import-linter, pytest with coverage, plus `render`/`slow`
markers and the strict docs build when relevant) green before merging; the merge flow of ADR-008; update PROGRESS.md
and, for design changes, DECISIONS.md; never commit secrets.

## Overview

| Milestone | Sessions | Count | Outcome |
| --- | --- | --- | --- |
| M0 Foundations | S01–S04 | 4 | Monorepo, tooling, CI, compat layer, `benchtop doctor`, docs skeleton |
| M1 Sim core | S05–S09 | 5 | SO-101 scene, `BenchtopEnv`, `reach`, LeRobot contract proven, viewer CLI |
| M2 Task suite | S10–S16 | 7 | 7 tasks, contact-gated checks, 8 perturbation families, EnvHub exports |
| M3 Experts and demos | S17–S22 | 6 | FK/IK, scripted experts ≥ 95%, demo datasets, teleop |
| M4 Grader | S23–S30 | 8 | Rubrics, runner, adapters, stats, taxonomy, reports, `benchtop grade`, v0.1.0 |
| M5 Dataset doctor | S31–S35 | 5 | 17 checks, reports, broken-dataset fixtures |
| M6 Reference baselines | S36–S40 | 5 | Reference datasets, CPU recipes, measured thresholds, GPU notebooks |
| M7 Projects P0–P4 | S41–S50 | 10 | Five complete projects |
| M8 Projects P5–P7 | S51–S57 | 7 | Diffusion, SmolVLA and debugging-clinic projects |
| M9 Hardware path | S58–S62 | 5 | Calib-check, real eval protocol, grid mat, P8 |
| M10 Hardening and v1.0 | S63–S70 | 8 | Fresh-machine tests, editorial passes, audits, launch kit, v1.0.0 |
| **Total** | | **70** | plus ~7 contingency sessions (10%) |

## Estimate and schedule

**Size.** 70 planned sessions + ~7 contingency = **~77 sessions**.

**Capacity (revised 23 Nov after the first measured runs).** Claude Max gives a usage allowance per rolling
5-hour window *and* a weekly allowance, shared with the owner's own Claude use. Builds run **only at night, 23:00–07:00
IST**, so each night has at most two windows (about 23:00–04:00 and 04:00–07:00). Measured on 23 Nov: one 5-hour
window is about 5% of the weekly allowance, so two windows a night is about 10% a week-night and the **5-hour window,
not the weekly allowance, is the binding limit**. Per token, the top model used roughly 4–6× more of the window
than `opus` (S01 on opus: complete in 8% of a window; S03–S05 on the top model: about 27% each, unfinished). The
runner therefore picks a model per session (default `opus`; the top model only for the hardest sessions; `sonnet`
for mechanical ones), keeps context small (CLAUDE.md "Working efficiently") and runs up to 3 lanes on a dependency
graph that also lets the M7–M10 project sessions run in parallel. Gates are unchanged for every model.

**Duration.** 68 sessions left after S02, plus ~7 contingency. A simulation of the nightly schedule (3 lanes, the
dependency graph, measured usage per model) gives 7–9 nights; with real-world friction (rebase conflicts, red CI,
partial sessions, contingency) we plan for **about 11 nights** (range 8–14), i.e. v1.0.0 ready around **4 Dec 2026**
(range 1–7 Dec). Release tags still wait for the owner's approval.

**Projected milestone dates** (expected case, morning the night's run ends):

| Milestone | Last session | Projected finish |
| --- | --- | --- |
| M0 Foundations | S04 | 24 Nov |
| M1 Sim core | S09 | 25–26 Nov |
| M2 Task suite | S16 | 27 Nov |
| M3 Experts and demos | S22 | 27–28 Nov |
| M4 Grader (v0.1.0) | S30 | 28–29 Nov |
| M5 Dataset doctor | S35 | 28 Nov |
| M6 Reference baselines | S40 | 29–30 Nov |
| M7 Projects P0–P4 | S50 | 2 Dec |
| M8 Projects P5–P7 | S57 | 3 Dec |
| M9 Hardware path | S62 | 2–3 Dec |
| M10 v1.0.0 | S70 | 4 Dec (1–7 Dec) |

**Daily schedule (IST, Asia/Kolkata):**

| Time (IST) | Run |
| --- | --- |
| 23:00–07:00 | Build lanes are topped up every 30 minutes; no new session starts after about 06:15 or when the 5-hour window is ≥ 85% used; everything stops and checkpoints at 07:00 |
| 07:00–23:00 | Reserved for the owner's own Claude use; no builds |
| 21:00 | Daily update to the owner (no build) |

If the owner uses Claude shortly before 23:00, that 5-hour window carries into the night and the first lanes stop
earlier. This is accepted: the owner's work always comes first. "Pause" stops everything until the next night.

**Runner rules** (implemented on the build machine, outside this repo):
- One session per lane at a time: `claude -p "/session SNN" --model <per-session model> --permission-mode
  bypassPermissions` inside the lane's clone, with a hard wall-clock cap of 4 h 30 min and a lock file per lane.
- After every run (normal end, usage limit or timeout), the runner checks the working tree: uncommitted changes on a
  `session/*` branch are scanned for secrets and with gitleaks, committed as `wip(<session>): runner checkpoint …`
  and pushed to that branch (never to `main`). If a pre-commit hook rejects half-finished work, the checkpoint is
  committed with hooks skipped on the session branch only and marked `(hooks skipped)`; the resuming session fixes
  the findings first, and nothing merges until hooks, the gate and CI are green. The next run resumes the branch.
- If a run reports a usage limit, the runner records it and does not retry; the next slot resumes.
- If the weekly allowance is exhausted, remaining slots that week are skipped automatically until the reset.
- If `main` is red or a blocker needs the owner, slots pause and the daily update asks for help.

**Guardrails beyond `.claude/settings.json`.** The deny list in `.claude/settings.json` is a seatbelt, not a lock:
`bypassPermissions` runs can reach the same effects by other commands. The real protections are: branch protection
on `main` (no force-push, CI required; decision D7), a GitHub login on the build machine without the `delete_repo`
scope (D7), no Hugging Face or PyPI credentials on the build machine, gitleaks in pre-commit and CI, and the runner
never pushing to `main` itself.

Milestone exit reviews: the last session of each milestone includes a review pass by the `reviewer` subagent over the
whole milestone diff, and fixes for anything it rates "must fix".

---

## M0 Foundations

### S01 · Monorepo skeleton and quality tooling
- **Goal**: a uv workspace with six packages that installs, lints, type-checks and tests cleanly.
- **Tasks**: root `pyproject.toml` (uv workspace, Python 3.12, dev dependency group); packages `benchtop-core`,
  `benchtop-sim`, `benchtop-grade`, `benchtop-data`, `benchtop-real`, `benchtop-lab` with `src/` layout, `py.typed`,
  `__version__`, hatchling build; ruff config (lint + format, line length 110), mypy strict config, pytest config
  (markers: `slow`, `network`, `gpu`, `hardware`, `render`, all deselected by default; coverage config);
  import-linter contracts from ARCHITECTURE §2 with `include_external_packages = true` and explicit forbidden
  contracts for `lerobot`/`torch`; `.pre-commit-config.yaml` (ruff, ruff-format, a *local* `uv run mypy` hook,
  end-of-file, trailing whitespace, check-added-large-files 1 MB, gitleaks); mypy `files`/`packages` config;
  PyTorch `cpu`/`cu` extras declared as conflicting with `[tool.uv.sources]` indexes (PLAN §11); `REUSE.toml` and
  `LICENSES/` (Apache-2.0, CC-BY-4.0) so `reuse lint` passes for JSON/YAML/notebooks/vendored assets; `Makefile` with
  `setup`, `lint`, `type`, `test`, `test-all`, `docs`; SPDX headers; accept ADR-004.
- **Acceptance**: `uv sync` works from a clean clone; `uv run benchtop --version` prints the version; all checks green;
  import-linter passes.
- **Tests**: one smoke test per package (import + version); a test that the CLI entry point runs.

### S02 · Continuous integration and repo hygiene
- **Goal**: every push and PR is checked automatically on GitHub Actions.
- **Tasks**: `ci.yml` (jobs: lint, typecheck, test on ubuntu-latest Python 3.12 and 3.13 with coverage gate,
  `render` job, `slow` job, import-linter, `reuse lint`, gitleaks); uv cache; `cpu` torch extra; `MUJOCO_GL=egl`
  with apt `libegl1 libegl-mesa0 libgl1-mesa-dri libosmesa6` (verify on ubuntu-latest);
  `nightly.yml` skeleton (scheduled, matrix incl. macos-latest); `.github/ISSUE_TEMPLATE/` (bug, task proposal, lesson
  feedback), `PULL_REQUEST_TEMPLATE.md`, `CODEOWNERS`, `dependabot.yml` (GitHub Actions + uv); `SECURITY.md`
  (GitHub private vulnerability reporting).
- **Acceptance**: CI green on the session PR (S02 is the first session that uses the PR merge flow); badges in
  README; workflows use pinned action SHAs and least-privilege `permissions:`; if the owner approved D7, branch
  protection on `main` (require CI, no force-push) is applied via `gh api`, otherwise it is listed as pending.
- **Tests**: CI itself; `actionlint` run locally via pre-commit hook.

### S03 · Compat layer v0 and `benchtop doctor`
- **Goal**: the LeRobot boundary exists and learners can check their machine.
- **Tasks**: add `lerobot==0.7.*` to `benchtop-core`; re-verify every LeRobot fact in the `lerobot-compat` skill and
  PLAN §2 against the installed package and write one contract test per fact (module paths, env contract, EnvHub
  loader flags, `PolicyOutput`, dataset v3 writer, Wilson helper); `benchtop_core.compat` with `lerobot_version()`,
  `open_dataset()` (read-only view: info, episodes, features, frames), stubs for `load_policy()`; environment
  fingerprint (`benchtop_core.fingerprint`); `benchtop doctor` checks: Python version, OS, CPU count, RAM, disk,
  MuJoCo import + offscreen render of a 64×64 test scene for the active `MUJOCO_GL`, LeRobot import + version range,
  ffmpeg availability, torch device (CPU/CUDA/MPS), optional HF login status (never prints tokens); `--json` output.
- **Acceptance**: `benchtop doctor` gives a clear pass/warn/fail table with a fix per failure; exit code reflects
  required checks.
- **Tests**: unit tests with each check mocked to pass/fail; compat contract test that opens a tiny dataset built in
  the test (no network); `network`-marked test that opens `lerobot/pusht` metadata.

### S04 · Docs site skeleton and release plumbing
- **Goal**: a published-ready docs site and automated changelog.
- **Tasks**: `mkdocs.yml` (Material, dark/light, search, mermaid via superfences, admonitions, tabs, code copy,
  edit-on-GitHub, CC BY 4.0 footer); nav for Start here / Projects / Concepts / Guides / Reference / Contributing;
  API reference; add the planning docs to the nav under a "Project" section **without moving the files** (CLAUDE.md
  and the `.claude` commands use their paths; links to files outside `docs/` use absolute GitHub URLs); decide
  Zensical vs Material 9.x (ADR-009); `docs.yml` workflow (build strict on PRs, deploy to GitHub Pages on `main`);
  `tools/bump_version.py` (one shared version) and git-cliff config generating `CHANGELOG.md`.
- **Acceptance**: `uv run mkdocs build --strict` passes locally and in CI; Pages deployment workflow ready (enabling
  Pages in repo settings is listed as a one-time manual step in PROGRESS.md if the API call is not permitted).
- **Tests**: docs build in CI; a link-check job (lychee) on nightly.

## M1 Simulation core

### S05 · SO-101 model and scene builder
- **Goal**: a correct, licensed SO-101 in a tabletop scene built with `MjSpec`.
- **Tasks**: vendor Menagerie `robotstudio_so101` at a pinned commit under
  `packages/benchtop-sim/src/benchtop_sim/assets/robotstudio_so101/` with its LICENSE and an `UPSTREAM.md` (commit,
  date, derivation); `SceneSpec`, `RobotSpec`, `CameraSpec`, `LightSpec`, `ObjectSpec` dataclasses; scene builder
  attaching the arm to a table mount, `front` and `wrist` cameras, lights, floor; unit conversion `degrees/gripper(0–100)
  ↔ ctrl` matching LeRobot's `so_follower(use_degrees=True)` and the official Space; joint limits table.
- **Acceptance**: model compiles; joint names/order exactly match LeRobot; conversion functions round-trip.
- **Tests**: compile test; joint name/order test; conversion round-trip (hypothesis); gripper 0/100 maps to closed/open
  jaw geometry; render test producing a non-empty 128×128 image (`render` marker).

### S06 · `BenchtopEnv` base and determinism
- **Goal**: a Gymnasium env that satisfies LeRobot's env contract.
- **Tasks**: `BenchtopEnv(gym.Env)` with configurable cameras, image size, fps (30), episode length; observation dict
  (`pixels`, `agent_pos`, optional `environment_state`); 6-D `Box` action in LeRobot units; `task_description`;
  `_max_episode_steps`; `info["is_success"]`, `info["metrics"]`, `info["stage"]`; lazy renderer; RNG streams via
  `SeedSequence.spawn`; `LEROBOT_SIM` dict; `close()` safety.
- **Acceptance**: `gymnasium.utils.env_checker.check_env` passes; same seed ⇒ identical observations.
- **Tests**: contract tests (dtypes, shapes, keys); determinism test; substep/timestep test; renderer-in-subprocess test.

### S07 · `reach` task, seed splits, performance
- **Goal**: the first complete task and the seed-split system.
- **Tasks**: `Task` ABC and `reach` (target sphere, hold 0.5 s, metrics); `SeedSplits` (train/val/exam with project
  salt, disjointness guaranteed); workspace regions (`in_distribution`, `extrapolation`); throughput benchmark script.
- **Acceptance**: random policy rarely succeeds (< 2%); a joint-space oracle (computed IK-free by sampling a reachable
  configuration first) succeeds 100%; performance meets PLAN §6.6 or the gap is recorded.
- **Tests**: success/hold unit tests incl. pass-through rejection; split disjointness (hypothesis); benchmark smoke.

### S08 · LeRobot integration proof
- **Goal**: prove LeRobot drives our env as an EnvHub env and as a sim robot.
- **Tasks**: `benchtop_sim.envhub.export(task, out_dir)`; generated `env.py` with `make_env`; contract test: load the
  exported folder through `compat.make_hub_env`, run a 2-episode `lerobot-eval` with a trivial policy, and drive it
  with `--robot.type=sim` for a few steps of keyboard-teleop-equivalent actions (programmatic); document the exact
  commands in `docs/guides/lerobot-commands.md`.
- **Acceptance**: LeRobot sees `observation.images.front`, `observation.images.wrist`, `observation.state`; eval
  reports a success rate; sim robot records a 2-episode dataset with `robot_type=so_follower`.
- **Tests**: the contract tests above (`slow` marker, run in CI).

### S09 · `benchtop envs` CLI, risk spikes and M1 review
- **Goal**: learners can list, inspect and watch tasks, and the two biggest technical risks are tested early.
- **Tasks**: `benchtop envs list`, `envs show <task>` (spaces, stages, metrics, regions), `envs view <task>`
  (interactive `mujoco.viewer` when a display exists, else renders an MP4 of a scripted sweep).
  **Spike A (grasp physics):** a hand-written joint-space trajectory grasps and lifts a 3 cm cube with the Menagerie
  SO-101 in ≥ 9/10 seeds; if not, record findings and options (contact params, cube friction, gripper actuator gains)
  in DECISIONS.md. **Spike B (CPU training budget):** time 200 `lerobot-train` steps of ACT with state +
  environment_state on a synthetic dataset on the 8-core build box and extrapolate P3's training time; record it.
  M1 review by the `reviewer` subagent; fix must-fix items.
- **Acceptance**: commands work headless and with a display; spike results recorded with go/no-go; review resolved.
- **Tests**: CLI tests via Typer's runner; MP4 written and non-empty; spike scripts kept under `tools/spikes/`.

## M2 Task suite

### S10 · Contact and placement primitives
- **Goal**: reusable, adversarially tested success primitives.
- **Tasks**: contact queries between named geoms/bodies; `is_grasped(obj)` (both jaws in contact, object above table);
  `is_resting(obj)` (speed < 1 cm/s for N steps); `in_region(obj, region)`; `released(obj)`; stage machine helper.
- **Acceptance**: primitives correct on constructed states, including thrown, tunnelling and held-above cases.
- **Tests**: ≥ 20 constructed-state tests covering positive and adversarial cases.

### S11 · `push` and `pick_lift`
- **Tasks**: both tasks with stages, metrics, randomization regions, instructions; per-task docs card generator.
- **Acceptance**: random policy < 2% success; hand-built oracle trajectories succeed.
- **Tests**: success/failure unit tests; stage progression tests; determinism.

### S12 · `pick_place` and `sort`
- **Tasks**: box object; `pick_place`; `sort` with 4 colored cubes and instruction templates (plus held-out paraphrases
  for P6); `wrong_object` metric.
- **Acceptance**: `sort` succeeds only for the named cube with all others outside the box.
- **Tests**: wrong-cube, two-cubes-in-box, held-above-box adversarial tests.

### S13 · `stack` and `obstacle_place`
- **Tasks**: `stack` with alignment tolerance; `obstacle_place` with a wall and `route ∈ {left, right, none}`
  detection; `collisions_with_obstacle` metric.
- **Acceptance**: route detection correct for constructed trajectories.
- **Tests**: alignment edge cases; route classification tests.

### S14 · Visual perturbations
- **Tasks**: `Perturbation` ABC; `lighting`, `camera_pose`, `textures`, `distractors`, each with severities 1–3;
  procedural textures generated at build time (no third-party images).
- **Acceptance**: perturbations change only what they claim (object placement unchanged across families for the same seed).
- **Tests**: independence tests; image statistics tests (e.g. mean brightness shifts for lighting).

### S15 · Physical perturbations and regions
- **Tasks**: `object_mass`, `friction`, `action_noise`, `latency`; extrapolation region sampling; perturbation registry
  and string spec parsing (`lighting:2`).
- **Acceptance**: physical perturbations measurably change dynamics; registry round-trips specs.
- **Tests**: dynamics change tests; parser tests; latency buffer tests.

### S16 · EnvHub exports for all tasks and M2 review
- **Tasks**: export all 7 tasks to `envhub/`; generated README task cards with licenses; compatibility note and test
  that our `pick_place` observation/action conventions match the official SO-101 Space's `LEROBOT_SIM`; milestone review.
- **Acceptance**: every export passes the S08 contract test.
- **Tests**: parametrized contract test over all tasks (`slow`).

## M3 Kinematics, experts, demonstrations

### S17 · Forward and inverse kinematics
- **Tasks**: FK from MuJoCo model (site poses); damped-least-squares IK with joint limits; mink-based IK wrapper;
  workspace reachability map tool.
- **Acceptance**: FK vs MuJoCo < 1 mm; IK median error < 5 mm on reachable targets.
- **Tests**: property tests (FK∘IK); benchmark of IK speed.

### S18 · Expert framework; `reach`, `push`, `pick_lift` experts
- **Tasks**: FSM expert base, Cartesian waypoint planner with smooth interpolation, gripper control; three experts.
- **Acceptance**: ≥ 95% success on 200 seeds each (*provisional*; record measured values).
- **Tests**: golden success-rate tests on fixed seeds (short in CI, full nightly).

### S19 · `pick_place`, `sort`, `stack` experts
- **Acceptance**: ≥ 95% on 200 seeds each; failure cases logged with seeds.
- **Tests**: golden tests.

### S20 · `obstacle_place` expert and expert analysis tool
- **Tasks**: expert with route sampled 50/50 (seeded); `benchtop envs expert-report` (success, failure seeds, videos).
- **Acceptance**: route balance within 45–55% over 200 episodes; ≥ 95% success.
- **Tests**: route balance test; report generation test.

### S21 · `benchtop demo` → LeRobotDataset v3
- **Tasks**: dataset writer through `compat` (features: state, env_state, images per camera, action, task string);
  per-episode metadata (seed, initial object poses, route); success-only filtering; image size options; resumable.
- **Acceptance**: datasets load in LeRobot and train for 10 steps with `lerobot-train` (ACT, CPU).
- **Tests**: tiny dataset round-trip; schema test; `slow` 10-step training smoke test.

### S22 · Teleop paths and M3 review
- **Goal**: learners without hardware can teleoperate and record; leader-arm owners can drive the sim twin.
- **Tasks**: `benchtop teleop <task>`: keyboard (and gamepad if `pygame`/`hidapi` is available) Cartesian control of the
  gripper through the S17 IK, gripper open/close, episode start/stop/discard keys, recording through the S21 dataset
  writer. (LeRobot 0.7's `keyboard` teleoperator emits raw key presses and `keyboard_ee` emits end-effector deltas, so
  neither drives a joint-space SO-101 sim directly; verified 23 Nov 2026.) Document and test the LeRobot route for
  leader owners: `lerobot-teleoperate/record --robot.type=sim ... --teleop.type=so101_leader`. M3 review.
- **Acceptance**: a 3-episode dataset recorded with scripted key events loads in LeRobot; docs page with the exact
  commands.
- **Tests**: key-event → action mapping tests; recording test with simulated key events; command-builder tests.

## M4 Grader

### S23 · Data models
- **Tasks**: Pydantic models for Rubric, Suite, Criterion, Results, SuiteResult, EpisodeRecord, Grade, Fingerprint;
  JSON Schema export to `docs/reference/schemas/`; schema migration hooks.
- **Tests**: validation tests incl. invalid rubrics; schema snapshot tests.

### S24 · Statistics
- **Tasks**: Wilson interval, Newcombe difference interval, episodes-needed helper; plain-language interpretation text.
- **Acceptance**: matches published reference values and LeRobot's Wilson output for the same counts.
- **Tests**: reference-value tests; hypothesis monotonicity tests.

### S25 · Suite runner
- **Tasks**: `SuiteRunner` with process pool, per-episode records, resume from partial results, Rich progress;
  `ExpertAdapter`, `CallableAdapter`, `ReplayAdapter`.
- **Acceptance**: identical results for 1 and N workers; resume works after interruption.
- **Tests**: worker-count invariance; resume test; adapter tests.

### S26 · LeRobot checkpoint adapter
- **Tasks**: `compat.load_policy`; `LeRobotCheckpointAdapter` (processors, `PolicyOutput` handling, chunk queues,
  rename map, device selection); input validation against rubric `policy_inputs`.
- **Acceptance**: a tiny randomly initialized ACT and Diffusion checkpoint (created in the test) run end to end.
- **Tests**: adapter tests per policy type (`slow`).

### S27 · Taxonomy, stage funnel, video capture
- **Tasks**: failure classifier from per-step info; stage funnel; failure/sampled-success video capture (MP4 + GIF thumbnail).
- **Tests**: classifier tests on synthetic traces; video tests.

### S28 · Grading and `benchtop grade`
- **Tasks**: criterion evaluation (metrics, artifacts, reflections, comparisons between named policies; cumulative
  grade levels), `benchtop grade <project> --policy ...` (repeatable `--policy name=path` for comparisons), `--suites`,
  `--episodes` override (marked "practice, not official"), `--verify results.json` (flags stale `task_version`);
  Dockerfile and `--batch` flow for instructors (no network, read-only mounts, pickles refused).
- **Tests**: grade evaluation tests; CLI tests; verify test.

### S29 · Report cards
- **Tasks**: Markdown and self-contained HTML reports (inline SVG charts: interval bars, stage funnel, robustness
  radar/bar, taxonomy), failure gallery, reproduction command; `benchtop report`.
- **Tests**: snapshot tests; HTML has no external URLs.

### S30 · Cross-check and v0.1.0
- **Tasks**: test that `benchtop grade` and `lerobot-eval` agree on success counts for the same checkpoint and seeds;
  milestone review; prepare `v0.1.0` release notes in `docs/project/releases/v0.1.0.md` (the tag and GitHub
  release are created by the owner or after the owner approves; no PyPI unless D4 approved); soft-launch drafts saved
  to `docs/launch/drafts/` (never posted).
- **Acceptance**: cross-check passes; release notes accurate.

## M5 Dataset doctor

### S31 · Doctor framework and D1–D5
- **Tasks**: check registry, severities, scoring, `DoctorReport` model; checks D1–D5 (PLAN §8).
- **Tests**: each check against synthetic good/bad datasets built in tests.

### S32 · D6–D9 and D12
- **Tests**: as above.

### S33 · D10 strategy consistency and D11 coverage
- **Tasks**: DTW-based trajectory clustering (no heavy deps; numba optional), coverage grid from sim metadata and a
  documented real-annotation format.
- **Tests**: mixed-strategy synthetic dataset detected; coverage numbers correct.

### S34 · Vision checks D13–D15, D16 stats, D17 calibration fingerprint
- **Tasks**: camera drift (feature matching vs reference frame), exposure and blur, frozen frames, stats sanity,
  calibration fingerprint.
- **Tests**: synthetic videos with injected drift, exposure jumps, frozen frames.

### S35 · `benchtop data check` and broken-dataset fixtures
- **Tasks**: CLI (local path or Hub id), Markdown/JSON reports, CI exit codes; generator for broken datasets (reused
  by P2 and P7); milestone review.
- **Tests**: CLI tests; each fixture triggers exactly its intended finding.

## M6 Reference baselines

### S36 · Reference datasets
- **Tasks**: generate scripted datasets for all tasks (state, env_state, 128×128 images) with dataset cards
  (CC BY 4.0); doctor reports for each; push to the Hub only if D3 approved, else keep locally and document.
- **Acceptance**: every reference dataset scores ≥ 95 in the doctor.

### S37 · CPU training recipes
- **Tasks**: minimal MLP-BC policy as a LeRobot "bring your own policy" plugin in `benchtop_core.policies.mlp`
  (ADR-007); ACT-state config
  (state + environment_state, no images); training scripts with fixed seeds; measure wall time on the 8-core build box.
- **Acceptance**: both train on CPU within the P3 budget or the budget/task is revised in DECISIONS.md.

### S38 · Calibrate P1–P3 and P7 thresholds
- **Tasks**: grade reference policies; set thresholds from measured results with margin; tiny CI checkpoints for golden tests.
- **Acceptance**: thresholds recorded with evidence in DECISIONS.md.

### S39 · GPU recipes and notebooks
- **Tasks**: Kaggle and Colab notebooks for ACT-vision, Diffusion, SmolVLA (T4 has no bf16: verify fp16 or fp32 +
  LoRA fits 16 GB; batch sizes for 16 GB); CPU dry-run with tiny step counts in CI; re-check Kaggle's current free GPU
  quota from Kaggle's own docs.
- **Acceptance**: notebooks execute top to bottom in CPU dry-run mode.

### S40 · GPU baselines and P4–P6 thresholds
- **Tasks**: if D2 approved, run reference trainings on Kaggle and record results; otherwise mark thresholds
  provisional and open "help wanted: verify on GPU" issues; milestone review.

## M7 Projects P0–P4 (two sessions each)

Session (a) for each project: lesson chapters, rubric.yaml, concept primers, common-failures page.
Session (b): starter code with TODOs, reference solution, tests for starter scaffolding and solution, notebook if
needed, docs integration, end-to-end grade of the solution reaching Distinction.

| Session | Project | Part |
| --- | --- | --- |
| S41 | P0 Setup and tour | (a) lesson, quiz, rubric |
| S42 | P0 | (b) quiz checker, starter, e2e |
| S43 | P1 Kinematics and a scripted expert | (a) |
| S44 | P1 | (b) |
| S45 | P2 Demonstrations that teach | (a) |
| S46 | P2 | (b) incl. planted-problem dataset |
| S47 | P3 Your first policy | (a) |
| S48 | P3 | (b) incl. scaling experiment script |
| S49 | P4 Seeing is believing | (a) |
| S50 | P4 | (b) incl. Kaggle/Colab notebooks; M7 review |

**Acceptance for every project**: a reviewer following only the lesson can complete it; the solution earns
Distinction in `benchtop grade`; `mkdocs build --strict` passes; the `curriculum-reviewer` subagent finds no must-fix issues.

## M8 Projects P5–P7

| Session | Project | Part |
| --- | --- | --- |
| S51 | P5 When averaging fails | (a) lesson, rubric, mode-coverage metric |
| S52 | P5 | (b) starter, solution, notebooks |
| S53 | P6 Language in the loop | (a) lesson, rubric, per-instruction confusion matrix |
| S54 | P6 | (b) starter, solution, notebooks |
| S55 | P7 Debugging clinic | `benchtop clinic` case generator (9 cases, deterministic) |
| S56 | P7 | lesson, diagnosis answer format and checker |
| S57 | P7 | starter, solution, e2e; M8 review |

## M9 Hardware path

### S58 · `benchtop-real` foundations and calib-check
- **Tasks**: read-only follower/leader access via compat; `benchtop real calib-check` (passive mode: user moves the
  leader, both arms read; active mode behind `--allow-motion` + safety checklist); report.
- **Tests**: everything against a mocked motor bus (`hardware` marker for real-device tests, never in CI).

### S59 · Real evaluation protocol
- **Tasks**: `benchtop real eval` interactive trial logger (zone, outcome, failure category, video path), Wilson
  interval, zone heatmap, `RealEvalLog` model; report-card integration.
- **Tests**: logger with scripted input; heatmap snapshot.

### S60 · Grid mat and hardware guides
- **Tasks**: generated SVG/PDF grid mat (A3, Letter, A4 tiled) with fiducial corners; camera placement and lighting
  guide; safety page.
- **Tests**: mat dimensions verified from the SVG.

### S61 · P8 lesson and rubric
- **Tasks**: P8 lesson (calibration, sim twin, recording, training, deployment with `lerobot-rollout`, evaluation).

### S62 · P8 integration and M9 review
- **Tasks**: semi-automatic grading flow for P8; milestone review.

## M10 Hardening and v1.0

| Session | Focus | Acceptance |
| --- | --- | --- |
| S63 | Fresh-machine end-to-end: clean Docker Ubuntu image and macOS CI run P0→P3 non-interactively | Quickstart to first graded result < 10 min (excluding downloads) |
| S64 | Nightly matrix, performance regression thresholds, upstream canary job against LeRobot `main` | Nightly green; canary opens issues on breakage |
| S65 | Editorial pass 1: P0–P4 lessons (clarity, accuracy, consistent terms, alt text) | `curriculum-reviewer` no must-fix |
| S66 | Editorial pass 2: P5–P8, concepts, reference, FAQ, troubleshooting | same |
| S67 | CLI UX pass: every error has cause + next step; `--help` examples; shell completion | UX checklist passes |
| S68 | Security and license audit: `reuse lint`, dependency license allowlist, gitleaks over history, SBOM | Clean audit report in `docs/project/audit.md` |
| S69 | Launch kit: demo GIFs, report-card screenshots, launch post drafts (HN, Reddit, X, Discord, HF blog) in `docs/launch/drafts/` | Drafts ready for Shiva's review; nothing posted |
| S70 | v1.0.0: version bump, changelog, release notes, docs deployed; tag/GitHub release after owner approval; PyPI only if D4 approved | Release ready; PROGRESS.md marked complete |

## Contingency

About 7 extra sessions are reserved (10%) for upstream breakages (LeRobot releases), physics tuning of grasps, and
review findings. Use them only through PROGRESS.md entries `S##x` with a reason.
