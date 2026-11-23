# Benchtop Lab: Product Specification and Plan

| | |
| --- | --- |
| Status | Planning (Phase 2). No product code yet. |
| Owner | @StardustModulator |
| Last updated | 23 Nov 2026 |
| Companion docs | [ARCHITECTURE.md](ARCHITECTURE.md), [MILESTONES.md](MILESTONES.md), [PROGRESS.md](PROGRESS.md), [DECISIONS.md](DECISIONS.md) |

Every number in this document marked *provisional* is calibrated in milestone M6 from measured reference baselines,
and the change is recorded in [DECISIONS.md](DECISIONS.md). We do not ship thresholds we have not measured.

---

## 1. Summary

Benchtop Lab is a free, open-source monorepo that teaches robot learning through graded, hands-on projects on the
SO-101 arm. It is **sim-first** (MuJoCo, runs on a laptop CPU) and **real-ready** (identical conventions to LeRobot's
`so_follower`, plus a hardware track). It is **built on LeRobot**, not a fork: we use LeRobot's datasets, policies,
training, sim-robot and EnvHub interfaces, and add the three things learners lack:

1. **A curriculum**: nine projects (P0 to P8), each with learning objectives, a lesson, starter code and a rubric.
2. **An honest grader**: held-out seeds, robustness suites, confidence intervals, failure taxonomy, report cards.
3. **Diagnostics**: a dataset doctor and a debugging clinic for the data and setup problems that cause most failures.

### 1.1 Goals

- G1. A learner with only a laptop can go from zero to a measured, working imitation-learning policy in simulation.
- G2. Every project produces a portfolio artifact backed by numbers that a reviewer can reproduce.
- G3. An SO-101 owner can carry the same workflow to the real arm and evaluate it with a standard protocol.
- G4. Instructors can adopt the projects as a course module with zero cost and automatic grading.
- G5. Engineering quality that earns trust: pinned, tested, documented, reproducible, CI on every change.

### 1.2 Non-goals for v1

- No hosted service, accounts, leaderboard server or paid tier. Everything runs on the learner's machine or free notebooks.
- No custom training framework. Training is `lerobot-train`; we provide configs and recipes.
- No reinforcement-learning track in v1 (HIL-SERL is a v2 candidate, see §17).
- No Isaac Sim / GPU-only simulators in the core path (laptop-first). LeIsaac is linked as an optional extension.
- No support for arms other than the SO-101 in v1 (the SO-100 works where conventions match, but is not graded).

---

## 2. Research findings (verified 23 Nov 2026)

| Fact | Evidence | Design consequence |
| --- | --- | --- |
| LeRobot has 29,042 GitHub stars and 6,120 forks. | [GitHub API](https://api.github.com/repos/huggingface/lerobot), 23 Nov 2026 | Large audience; LeRobot conventions are the ones to teach. |
| LeRobot 0.7.0 is current (5 Nov 2026), Python ≥ 3.12, Apache-2.0. | [PyPI](https://pypi.org/project/lerobot/), [release notes](https://github.com/huggingface/lerobot/releases/tag/v0.7.0) | Pin `lerobot==0.7.*`, Python 3.12. Isolate LeRobot calls in one compat module; LeRobot ships breaking changes every minor release. |
| LeRobot 0.7 runs any simulator as a batched env (`lerobot-eval`) or as a **sim robot** (`--robot.type=sim`) usable with `lerobot-record`, `-teleoperate`, `-rollout`, `-replay`. | [Simulation docs](https://huggingface.co/docs/lerobot/simulation) | Our tasks implement the LeRobot env contract so every LeRobot command works on them. |
| EnvHub: any Hugging Face Space with an `env.py` exposing `make_env` is a LeRobot environment. | [EnvHub docs](https://huggingface.co/docs/lerobot/envhub) | Each Benchtop task is exported as an EnvHub-compatible folder (local path works without publishing). |
| `lerobot-eval` now reports success with a 95% Wilson interval. | v0.7.0 release blog | Our statistics agree with LeRobot's; we add held-out splits, perturbation suites and per-stage breakdowns. |
| An official **SO-101 tabletop MuJoCo** EnvHub Space exists (4 cubes into a box; 30 fps; joint degrees, gripper 0 to 100; cameras `front`, `wrist`). Published 19 Nov 2026, 1 like. | [Space](https://huggingface.co/spaces/lerobot/so101-tabletop-mujoco) | Match its conventions exactly (camera names, units, `LEROBOT_SIM` semantics `so101-joint-degrees-v1`). It is one task with no curriculum; we provide a graded progression and cross-evaluate on it. |
| SO-101 MJCF in MuJoCo Menagerie (`robotstudio_so101`), Apache-2.0, with primitive collision geoms tuned for manipulation. | [Menagerie](https://github.com/google-deepmind/mujoco_menagerie/tree/main/robotstudio_so101) | Vendor it at a pinned commit, keep its LICENSE. |
| Upstream SO-101 URDF/MJCF: TheRobotStudio/SO-ARM100, Apache-2.0, ~8.2k stars; two calibration conventions (new = mid-range zero). | [SO-ARM100 Simulation/SO101](https://github.com/TheRobotStudio/SO-ARM100/tree/main/Simulation/SO101) | Use the "new calibration" convention, same as LeRobot and Menagerie. Teach calibration explicitly in P1/P8. |
| MuJoCo 4.0.1 (Apache-2.0), mink 1.4.0 IK (Apache-2.0), Gymnasium 1.4.0 (MIT). `lerobot==0.7.0 + mujoco==4.0.1 + mink` resolves cleanly on Python 3.12 (torch 2.15). | PyPI; local `uv pip compile` run | Stack is compatible today. |
| gym-hil (LeRobot's HIL-SERL sim) is a Franka Panda env and its docs ask for an NVIDIA GPU. | [hilserl_sim docs](https://huggingface.co/docs/lerobot/hilserl_sim) | Not used for v1. |
| LeIsaac (SO-101 in Isaac Sim, Apache-2.0) needs an RTX GPU or cloud. | [LeIsaac](https://github.com/LightwheelAI/leisaac) | Optional link only. |
| Policies in LeRobot: ACT, Diffusion, VQ-BeT, TD-MPC, SmolVLA (450M, Apache-2.0), π0 / π0.5 (~3.5B, Gemma license), GR00T, X-VLA and many large VLAs/WAMs. π0.5 fine-tuning recipe is "sized for a single 80 GB GPU". SmolVLA: "~4 h for 20k steps on one A100". ACT: "a few hours for 100k steps on a single GPU". | LeRobot docs, HF model cards | Core path: ACT and Diffusion (fit 16 GB, state-only variants on CPU). VLA project uses **SmolVLA only** (Apache-2.0, fits free T4). π0/π0.5 mentioned as further reading due to size and Gemma license. |
| Free GPUs: Kaggle gives phone-verified accounts **2× T4 16 GB, ~30 GPU h/week, 12 h max per run** (P100 retired 15 Sep 2026). Google Colab free tier offers a T4 intermittently. | [Kaggle docs: GPU quota](https://www.kaggle.com/docs/efficient-gpu-usage) ("30 hours or sometimes higher"); T4 ×2 and P100 retirement per [this Nov 2026 guide](https://fastero.com/blog/kaggle-gpu), re-checked in S39 | GPU projects ship Kaggle and Colab notebooks and are sized to finish within one 12 h Kaggle run (target ≤ 4 h). |
| HF Robotics Course: units 0 to 2 published; imitation learning, RL and foundation-model units "coming soon" (Oct 2026). | [HF Robotics Course](https://huggingface.co/learn/robotics-course/unit0/1) | Complement it: we are the hands-on, graded lab to its conceptual course. Link to it for theory. |
| Seeed: free 22-chapter SO-ARM course and a 17 Nov 2026 troubleshooting guide. | [Seeed course](https://wiki.seeedstudio.com/robotics/soarm_physical_ai_course_introduction/), [guide](https://www.seeedstudio.com/blog/2026/11/17/so-arm101-lerobot-troubleshooting-guide/) | Workflow is covered; grading and diagnosis are not. Link, do not duplicate. |
| Single-task SO-101 MuJoCo pipelines exist (EE5108 `lerobot_mujoco_sim`, `lerobot-so101-pick-and-place`, rocPAI SimStudio Lab 01, a 25-student Udemy course). One reports ACT 64% vs SmolVLA 22% on full-range cube spawns. | [EE5108](https://github.com/EE5108-DigitalTwins/lerobot_mujoco_sim), [rocPAI](https://rocpai-forge.github.io/en/posts/so101-simstudio-lab01/) | The "collect → train → eval one task" loop is commoditized. Our value is the progression, the grading rigor and the diagnostics. |
| Learner pain is mostly data/setup: calibration offsets (a 17.5° wrist offset → 0% grasp, 80% after fix), leader arm visible in camera (shortcut learning), mixed strategies averaged by ACT, moved cameras, thin workspace coverage, "what success rate should I expect from 50 episodes?". | [PyCon 2026 talk](https://maeste.it/pycon2026-so101/final/presentation/slides.html), [HF forum](https://discuss.huggingface.co/t/what-is-the-expected-success-rate-for-a-act-trained-model-using-50-episodes/178517), [AY-Robots](https://www.ay-robots.com/train/act-on-so-101), [lerobot#2213](https://github.com/huggingface/lerobot/issues/2213) | These become P2 (data), P7 (debugging clinic), the dataset doctor checks, and the calibration checker in P8. |

### 2.1 Positioning in one sentence

> The HF Robotics Course teaches the ideas, LeRobot gives you the tools, Seeed shows you the workflow.
> **Benchtop Lab makes you do it, measures whether it worked, and teaches you to fix it when it did not.**

---

## 3. Users

| Persona | Situation | What they need from us | Success looks like |
| --- | --- | --- | --- |
| **Ana, ML engineer** | Strong PyTorch, zero robotics, laptop with no GPU. | A ramp from ML concepts to robot concepts; CPU-feasible projects; honest metrics. | Finishes P0 to P3 in a weekend; understands why her policy fails off-distribution. |
| **Ravi, MS robotics student** | Knows kinematics; wants a portfolio project for internships. | Rigorous, reproducible results and a report card reviewers trust. | Report cards for P4 to P6 linked from his CV; a real-arm result in P8. |
| **Mei, SO-101 owner** | Built the kit, recorded 50 episodes, 0 to 20% success. | Diagnosis: is it calibration, cameras, data or the model? | Dataset doctor finds the problem; success climbs on a standard protocol. |
| **Prof. Okafor, instructor** | Teaches a robot-learning elective; no budget. | Ready labs, autograding, no hardware dependency, stable versions. | Uses P0 to P5 as weekly labs for a 40-student class. |

Prerequisites we assume: Python, NumPy, basic PyTorch training loops. We teach everything robot-specific.

---

## 4. v1 scope

### 4.1 In scope (v1.0.0)

- `benchtop-sim`: 7 tasks (§6), seeded randomization, train/val/exam seed splits, 8 perturbation families, contact-gated
  success and per-stage checks, LeRobot env contract, EnvHub export, CPU rendering, determinism tests.
- `benchtop-sim` experts: IK-based scripted experts for every task (≥ 95% success, *provisional*); `benchtop teleop`
  (keyboard and gamepad Cartesian control through our IK, recording LeRobotDataset v3); `so101_leader` teleop into
  sim through LeRobot's sim robot for hardware owners.
- `benchtop-grade`: rubric-driven protocols, policy adapters (LeRobot checkpoints, Python callables, scripted experts),
  Wilson intervals, per-stage and per-perturbation breakdowns, failure taxonomy, failure gallery (MP4/GIF),
  `results.json` (versioned schema), Markdown and self-contained HTML report cards.
- `benchtop-data`: dataset doctor with 17 checks (§8), JSON + Markdown report, CI-friendly exit codes.
- `benchtop` CLI: `doctor`, `envs`, `demo`, `teleop`, `grade`, `report`, `data check`, `clinic`, `real` (hardware).
- Projects P0 to P8 with lessons, starters, exercises, rubrics, solutions, and notebooks for GPU projects.
- Docs site (MkDocs Material, GitHub Pages) with the lessons, CLI reference, API reference and FAQ.
- Reference baselines: scripted-expert datasets and measured reference results for every project (CPU ones
  measured on our build box; GPU ones measured on a free Kaggle T4 if Shiva approves an account, see §18).
- Hardware path: calibration checker, real evaluation protocol, printable grid mat (SVG/PDF), P8 lesson.

### 4.2 Out of scope for v1 (candidates for v1.x / v2)

RL track (HIL-SERL, sim RL with MuJoCo Playground/MJX), bimanual SO-101, LeKiwi mobile manipulation, a public
leaderboard Space, translations, Isaac Sim tasks, video lessons, large VLAs (π0.5, GR00T) beyond further-reading notes.

---

## 5. Curriculum design

### 5.1 Pedagogy

- **Backward design.** Each project starts from what the learner must be able to *do* and how we will *measure* it,
  then the lesson teaches exactly that.
- **Predict, run, explain.** Before each experiment the lesson asks the learner to predict the outcome
  (e.g. "what happens to success if you halve the demos?"), then run it, then explain the gap. Predictions are
  recorded in the report card's reflection section.
- **One new idea per project.** Each project changes one major variable (state → vision, unimodal → multimodal,
  single-task → language-conditioned, sim → real), so cause and effect stay visible.
- **Failure is content.** Every project has a "common failures" section generated from real failure galleries.
- **Honest numbers.** Every claim is a success rate with an interval on held-out seeds. Learners learn to distrust
  single videos and training loss.
- **Time-boxed.** Each project targets 3 to 8 hours of learner time, with compute runs that fit a free notebook.

### 5.2 Project anatomy (identical for every project)

```
projects/pN_<slug>/
  README.md            # objectives, prerequisites, time and compute budget, deliverables
  lesson/              # Markdown chapters rendered on the docs site (CC BY 4.0)
  starter/             # code with TODOs the learner completes
  solution/            # reference solution (open; the honour system applies)
  configs/             # lerobot-train configs and benchtop configs
  rubric.yaml          # what the grader runs and the pass thresholds
  notebooks/           # Kaggle and Colab notebooks for GPU projects
  tests/               # tests for starter scaffolding and the reference solution
```

Grades are **Pass**, **Merit** and **Distinction**. Pass means the core objective works on held-out seeds;
Merit adds robustness; Distinction requires a stretch result plus a written analysis.

### 5.3 The projects

Thresholds below are *provisional* and use the **lower bound of the 95% Wilson interval** unless stated, so a lucky
small sample cannot pass.

#### P0: Setup and tour

- **Objectives.** Install the stack; explain the SO-101's 6 joints, units and the "new calibration" zero; run a sim
  robot with LeRobot's own commands; inspect a LeRobotDataset v3 (episodes, features, stats, videos).
- **Lesson.** Anatomy of the SO-101; LeRobot's robot/teleop/dataset/policy concepts; observation and action contract;
  how sim robots mirror real ones.
- **Deliverables.** `benchtop doctor` report; a 5-episode keyboard-teleop dataset of the `reach` task recorded with
  `benchtop teleop` (Cartesian keyboard control through our IK; LeRobot's own `keyboard` teleoperator emits key
  presses, not joint targets, so it cannot drive an SO-101 sim directly); a replay of one episode with
  `lerobot-replay --robot.type=sim`; answers to a short "tour quiz" (auto-checked JSON).
- **Graded.** Doctor passes all required checks; dataset loads and has 5 episodes with valid schema; quiz ≥ 80%.
- **Compute.** Any laptop, < 1 h.

#### P1: Kinematics and a scripted expert

- **Objectives.** Implement forward kinematics from the MJCF; solve IK with damped least squares and with mink;
  build a finite-state-machine expert for `pick_lift`; explain why a hand-written expert breaks under perturbation.
- **Lesson.** Frames and transforms, the SO-101's kinematic chain, Jacobians, singularities, joint limits; FSM design;
  degrees vs radians; gripper 0 to 100 mapping.
- **Deliverables.** `fk()` and `ik()` implementations; an expert policy class.
- **Graded.** FK matches MuJoCo to < 1 mm on 1,000 random configurations; IK reaches 200 targets with median error
  < 5 mm and ≥ 95% within 1 cm; expert `pick_lift` success lower bound ≥ 85% on 100 exam seeds (Pass);
  lower bound ≥ 70% under the `object_mass` and `friction` perturbations (Merit); analysis of failure modes (Distinction).
- **Compute.** CPU, < 30 min.

#### P2: Demonstrations that teach

- **Objectives.** Generate datasets with the scripted expert and with teleop; understand what makes demonstrations
  learnable (consistency, coverage, no idle frames, success only); use the dataset doctor.
- **Lesson.** LeRobotDataset v3 internals; coverage vs consistency; why ACT averages contradictory demos; episode
  trimming; the doctor's checks and what each failure costs a policy.
- **Deliverables.** A 100-episode `pick_place` dataset that passes the quality gate; a "bad" dataset with three
  planted problems that the learner finds with the doctor and explains.
- **Graded.** Dataset doctor score ≥ 90/100 with zero errors; workspace coverage ≥ 80% of the training region's grid
  cells; planted-problem diagnosis 3/3 correct.
- **Compute.** CPU, about 1 h (rendering included).

#### P3: Your first policy

- **Objectives.** Train behavior cloning from state (MLP), then ACT from state plus object pose; observe compounding
  error; understand action chunking and temporal ensembling; read a grader report.
- **Lesson.** BC as supervised learning; covariate shift; chunking; normalization statistics; why training loss is not
  success; reading confidence intervals.
- **Deliverables.** Two trained checkpoints (MLP-BC, ACT-state) on `pick_place`; a data-scaling experiment
  (25 / 50 / 100 demos) with predictions recorded beforehand.
- **Graded.** ACT-state success lower bound ≥ 60% on 100 exam seeds (Pass); MLP vs ACT comparison with intervals and a
  scaling plot (Merit); ≥ 80% plus written explanation of the scaling result (Distinction).
- **Compute.** CPU-only by design: state-based policies, < 45 min training on 8 cores (*provisional*, measured in M6).

#### P4: Seeing is believing

- **Objectives.** Train ACT from images (front + wrist) and state; use augmentation; measure robustness to lighting,
  camera pose, distractors and textures; learn why the wrist camera matters.
- **Lesson.** Visual encoders, image normalization, augmentation in LeRobot 0.7 (batched GPU transforms), shortcut
  learning, out-of-distribution evaluation.
- **Deliverables.** Vision ACT checkpoint; ablation front-only vs front+wrist; robustness profile.
- **Graded.** Nominal success lower bound ≥ 60% (Pass); mean lower bound ≥ 40% across the `lighting`, `camera_pose`
  and `distractors` suites (Merit); ablation analysis (Distinction).
- **Compute.** GPU. Kaggle T4 notebook sized to ≤ 4 h. CPU path exists but is slow and documented as such.

#### P5: When averaging fails

- **Objectives.** See mode averaging in action and fix it with Diffusion Policy; measure multimodality.
- **Task.** `obstacle_place`: an obstacle between start and goal; demos go left or right with equal probability.
- **Lesson.** Multimodal action distributions; MSE regression to the mean; ACT's CVAE; diffusion and denoising;
  inference speed vs quality.
- **Deliverables.** ACT and Diffusion checkpoints on the same data; comparison report.
- **Graded.** Diffusion success lower bound ≥ 60% (Pass); mode coverage: both routes used, each between 25% and 75%
  of successful episodes (Merit); collision-with-obstacle rate analysis comparing ACT and Diffusion (Distinction).
- **Compute.** GPU (state-only variant on CPU allowed for Pass).

#### P6: Language in the loop

- **Objectives.** Fine-tune SmolVLA for language-conditioned sorting; measure per-instruction success; understand
  pretrained VLAs, tokenized language and action experts.
- **Task.** `sort`: "put the {red, green, blue, yellow} cube in the box" with all cubes present.
- **Lesson.** VLA architecture; fine-tuning vs from scratch; language grounding failures; LoRA/PEFT in LeRobot 0.7.
- **Deliverables.** Fine-tuned SmolVLA; per-instruction confusion matrix (which cube was moved for which instruction).
- **Graded.** Overall success lower bound ≥ 50% (Pass); every instruction ≥ 40% and wrong-object rate ≤ 10% (Merit);
  held-out paraphrased instructions analysis (Distinction).
- **Compute.** GPU, Kaggle T4 (fp16, small batch, LoRA if needed), ≤ 6 h; *provisional*, verified in M6.

#### P7: Debugging clinic

- **Objectives.** Diagnose the failures that dominate real projects, without being told what is wrong.
- **Cases** (generated deterministically by `benchtop clinic`): calibration offset on one joint; camera moved between
  training and evaluation; "leader arm visible" shortcut (a distractor correlated with the goal in training only);
  two grasp strategies mixed; wrong fps metadata; stale normalization statistics; action/state misalignment by a few
  frames; idle frames at episode start; gripper units flipped.
- **Deliverables.** For each of 6 assigned cases: a diagnosis (multiple choice + free text) and a fix that restores
  success.
- **Graded.** ≥ 5 of 6 correct diagnoses (Pass); fixes restore the success point estimate to within 10 percentage
  points of the clean baseline for ≥ 4 cases (Merit); a new case contributed as a PR (Distinction).
- **Compute.** CPU (state-based cases); one optional vision case.

#### P8: Real arm capstone (optional, hardware)

- **Objectives.** Calibrate and verify; teleoperate the sim twin with the real leader arm; record, train and deploy
  a policy on the real SO-101; evaluate with a standard protocol.
- **Lesson.** Calibration and its failure modes; camera placement; lighting control; sim vs real gaps; safe operation.
- **Deliverables.** Calibration check report; real dataset (doctor-checked); real evaluation log of 20 trials on the
  printable grid mat with video; report card.
- **Graded** (semi-automatic, self-reported with video evidence). Calibration offsets < 3° on all joints; dataset
  doctor passes; real success lower bound ≥ 40% on 20 trials (Pass); success map across the 9 grid zones (Merit);
  sim vs real comparison (Distinction).

### 5.4 Learning-path options

- **Laptop path (no GPU):** P0, P1, P2, P3, P7 (+ P5 state variant).
- **Full sim path:** P0 to P7.
- **Hardware path:** full sim path + P8.
- **Instructor module (6 weeks):** P0+P1, P2, P3, P4, P5, P7.

---

## 6. Simulation environment design (`benchtop-sim`)

### 6.1 Conventions (must match LeRobot's SO-101 follower and the official MuJoCo Space)

| Item | Value |
| --- | --- |
| Joints | `shoulder_pan`, `shoulder_lift`, `elbow_flex`, `wrist_flex`, `wrist_roll`, `gripper` |
| State / action names | `<joint>.pos` |
| Units | Degrees for arm joints (new calibration, mid-range zero); gripper 0 (closed) to 100 (open) |
| Control | Absolute joint position targets, 30 fps, physics substeps computed from the timestep |
| Cameras | `front` (scene) and `wrist` (gripper); Benchtop default 128×128 RGB (CPU-friendly), 480×640 available to match the official Space |
| `LEROBOT_SIM` | `{"fps": 30, "control_mode": "position", "semantics": "so101-joint-degrees-v1", "state_names": [<joint>.pos ×6], "action_names": [<joint>.pos ×6], "robot_type": "so_follower"}` (the official Space's key set; re-verified in S08) |
| Observation | `pixels` (dict of HWC uint8), `agent_pos` (6 float32), optional `environment_state` (privileged object poses) |
| Info | `is_success` every step; `metrics` dict (see §6.5); `stage` (furthest stage reached) |
| Episode semantics | The success condition (including hold and resting windows) is evaluated every step. On the first step it holds, `is_success=True` and `terminated=True`. An episode is successful iff it terminated with success; otherwise it is `truncated` at the step limit. The grader and `lerobot-eval` therefore count the same thing. Each episode's seed is explicit; the cross-check in S30 maps LeRobot's per-batch seeding to our seeds (verified in S08). |

### 6.2 Task suite

| Task | Description | Stages | Episode length | Used in |
| --- | --- | --- | --- | --- |
| `reach` | Move the gripper tip to a randomized target sphere and hold for 0.5 s | reach, hold | 150 steps (5 s) | P0, P1 |
| `push` | Push a cube into a goal region on the table | contact, push, settle | 300 | P1, P3 |
| `pick_lift` | Grasp a cube and lift it 5 cm, hold 1 s | reach, grasp, lift, hold | 300 | P1, P3 |
| `pick_place` | Pick a cube and place it in a box | reach, grasp, transport, place, release | 450 | P2, P3, P4, P7 |
| `sort` | Language-conditioned: move the named cube (of 4) into the box | reach, grasp (correct object), transport, place | 450 | P6 |
| `stack` | Stack cube A on cube B | reach, grasp, transport, align, release | 450 | stretch tasks |
| `obstacle_place` | Place a cube on the far side of a wall; two equally valid routes | reach, grasp, route, place | 450 | P5 |

### 6.3 Success checks that cannot be faked

- **Contact-gated grasp:** a grasp counts only with both jaws in contact with the object and the object off the table.
- **Resting placement:** a placed object must be inside the target region, below a height threshold, with linear
  speed < 1 cm/s for 10 consecutive steps, and *not in contact with the gripper* (released).
- **Correct object (sort):** success requires the named cube in the box and every other cube outside it.
- **Hold checks:** `reach` and `pick_lift` require holding the state, not passing through it.
- Each check is a pure function of MuJoCo state, unit-tested with constructed states (positive and adversarial cases:
  object thrown in, object held above the box, wrong cube, tunnelling).

### 6.4 Randomization, splits and perturbations

- **Nominal randomization:** object poses (x, y, yaw) within a task-specific region, initial joints (± 3°), camera
  jitter (± 1 cm), box pose.
- **Seed splits:** `train` (seeds used to generate demos), `val` (for the learner), `exam` (for grading). Exam seeds
  are derived deterministically from a project salt and are disjoint from train/val by construction; a unit test
  enforces disjointness. Since everything is open source, the exam split guards against *accidental* overfitting,
  not cheating; the report card records the split used.
- **Workspace regions:** `in_distribution` (the demo region) and `extrapolation` (a ring outside it) for coverage studies.
- **Perturbation families (8):** `lighting` (intensity, direction, color), `camera_pose` (± 2 to 5 cm, ± 3 to 8°),
  `distractors` (1 to 3 unrelated objects), `textures` (table and object textures), `object_mass`, `friction`,
  `action_noise`, and `latency` (1 to 3 frames of delay). Each family has three severities.
- **How perturbations apply:** families that only change `MjModel` numeric fields (lighting, camera pose, mass,
  friction) are applied in place at `reset()` and restored from a pristine copy before the next episode, so no state
  leaks between episodes. Families that change geometry or textures (distractors, textures) select from a small set of
  pre-compiled model variants cached per (task, family, severity); the one-off compile cost is excluded from the
  `reset()` budget. Step-level families (`action_noise`, `latency`) keep their buffers in the perturbation object and
  are cleared by `Perturbation.reset()`.

### 6.5 Metrics emitted per episode

`success`, `stage_reached`, `time_to_success`, `path_length_m`, `joint_jerk`, `max_contact_force`,
`collisions_with_obstacle`, `drops`, `wrong_object`, `final_object_error_m`, `route` (for `obstacle_place`).

### 6.6 Performance budget

- State-only step (no rendering): ≥ 2,000 steps/s on one CPU core (*provisional*).
- Rendering two 128×128 cameras on a CPU-only machine (Mesa llvmpipe EGL or OSMesa): target ≥ 60 fps per process;
  480×640 is slower and documented as such. All rendering numbers are measured in S07 and recorded in DECISIONS.md.
- `reset()` < 20 ms. Deterministic given a seed (bitwise-equal observations across runs on the same machine).
- Headless rendering on Linux via `MUJOCO_GL=egl`, fallback `osmesa`; macOS via `glfw`/`cgl`.

---

## 7. Grader design (`benchtop-grade`)

### 7.1 Concepts

- **Rubric** (`rubric.yaml` in each project): which suites to run, how many episodes, thresholds per grade, required
  artifacts and reflection questions.
- **Suite:** a task + seed split + perturbation family/severity + episode count.
- **Policy adapter:** turns anything into `act(observation) -> action`: LeRobot pretrained checkpoints (via the compat
  layer and LeRobot's processors), a Python import path, the scripted experts, or a recorded action replay.
- **Run:** executing all suites of a rubric for one policy produces a `results.json` and artifacts.

### 7.2 Statistics

- Success: count, rate and **95% Wilson interval** (the same method as `lerobot.utils.eval_stats.wilson_interval`,
  verified by a cross-check test).
- Success-rate thresholds apply to the Wilson **lower bound** unless a criterion explicitly says "point estimate";
  the report explains this in plain language (e.g. on 20 real trials, a lower bound ≥ 0.40 needs at least 13 successes).
- Grade levels are cumulative: Merit requires Pass, Distinction requires Merit.
- Comparisons (P3, P4, P5): two-proportion difference with a Newcombe interval, never "A beats B" on overlapping CIs.
- Episodes per suite default to 100 for CPU projects and 50 for GPU projects (*provisional*); the report shows how
  wide the interval is and how many more episodes would narrow it.

### 7.3 Outputs

- `results.json` (schema in [ARCHITECTURE.md](ARCHITECTURE.md#5-data-model)): versioned, with an environment
  fingerprint (OS, CPU/GPU, Python, package versions, git SHA, MuJoCo version), checkpoint SHA-256, seeds, per-episode
  records and the grade.
- `report.md` and a self-contained `report.html` (no external assets): headline grade, success with interval bars,
  per-stage funnel, per-perturbation robustness chart, failure taxonomy, failure gallery (first frames + GIFs),
  reflection answers, reproduction command.
- `artifacts/`: episode videos (failures and a sample of successes), plots.

### 7.4 Failure taxonomy

Automatically assigned from per-step info: `never_reached`, `missed_grasp`, `dropped_in_transport`, `misplaced`,
`not_released`, `wrong_object`, `collision`, `timeout_hesitation` (low motion), `jitter` (high jerk), `unstable_grasp`.
Each category links to a docs page explaining typical causes and fixes.

### 7.5 Comparisons

P3 to P5 compare two policies. A comparison run grades both policies on the same suites and seeds and reports the
Newcombe interval for the difference; `results.json` can hold several policies and their comparisons (ARCHITECTURE §5).

### 7.6 Trust and isolation

Grading executes code: learner checkpoints (loaded from safetensors through LeRobot, the safe path), `CallableAdapter`
targets (`module:object`, arbitrary Python) and EnvHub environments (`trust_remote_code`). On a learner's own machine
this is their own code. For instructors grading many submissions, v1 ships a Docker image and a documented
`benchtop grade --batch submissions/` flow that runs each submission in a container with no network and read-only
mounts; pickled checkpoints are refused.

### 7.7 Reproducibility and verification

`benchtop grade --verify results.json` re-runs a random subset of episodes from the recorded seeds and checkpoint and
checks that outcomes match (deterministic on the same platform; tolerance documented across platforms).

---

## 8. Dataset doctor (`benchtop-data`)

Works on any LeRobotDataset v3 (local path or Hub repo id), sim or real. Each check has a severity (error, warning,
info), a score contribution, an explanation and a fix.

| # | Check | Catches |
| --- | --- | --- |
| D1 | Schema and features | Missing `observation.state`/`action`, wrong names or units for `so_follower` |
| D2 | FPS and timestamps | Metadata fps mismatch, gaps, jitter, duplicate timestamps |
| D3 | Episode length outliers | Abandoned or overly long episodes |
| D4 | Idle frames | Static stretches at start/end (policy learns to wait) |
| D5 | Joint limits and units | Values outside SO-101 ranges, radians recorded as degrees, flipped gripper |
| D6 | Action-state lag | Action leads/lags state by more than k frames (misalignment) |
| D7 | Action smoothness | Jerk and spike outliers (teleop jitter) |
| D8 | Gripper chatter | Rapid open/close oscillation |
| D9 | Success labels | Failed episodes included (sim: from info; real: from annotations) |
| D10 | Strategy consistency | Clusters of trajectories (DTW + clustering) indicating mixed strategies |
| D11 | Workspace coverage | Grid coverage of initial object positions (sim metadata or annotated real start frames) |
| D12 | Start-pose diversity | All episodes start from the identical pose |
| D13 | Camera stability | Camera pose drift across episodes (feature matching vs a reference frame) |
| D14 | Exposure and blur | Brightness shifts, auto-exposure hunting, motion blur |
| D15 | Frozen frames | Duplicate consecutive frames (camera stalls) |
| D16 | Statistics sanity | `meta/stats.json` consistent with data; quantiles present for policies that need them |
| D17 | Calibration fingerprint | Joint-offset signature vs a reference dataset from the same arm |

Output: a 0 to 100 score, a list of findings, JSON for CI, and a Markdown report with plots.

---

## 9. Hardware path

- **Supported hardware:** SO-101 leader + follower (Feetech STS3215), one front USB camera, optional wrist camera.
- **Calibration checker:** `benchtop real calib-check` has two parts. *Relative*: reads leader and follower while the
  user moves the leader (or moves both through matched poses), reports per-joint offset mean/max and flags joints
  above 3°. *Absolute*: the user places the follower in three physically defined reference poses using printed
  alignment marks on the grid mat (folded rest pose, gripper touching two marked points), which catches offsets that
  leader and follower share. Read-only by default;
  any motion requires an explicit `--allow-motion` flag and shows a safety checklist first.
- **Sim twin:** `lerobot-teleoperate --robot.type=sim ... --teleop.type=so101_leader` drives our sim with the real
  leader, so leader-only owners can record sim datasets.
- **Real evaluation protocol:** a printable A3/Letter grid mat (3×3 zones, SVG + PDF), 20 trials (≈ 2 per zone + 2
  random), fixed reset procedure, a CLI that records each trial's zone and outcome, computes the Wilson interval and
  renders a zone heatmap. Video evidence path is stored in the results.
- **Safety:** torque limits stay LeRobot defaults; documentation covers pinch points, emergency stop (unplug power),
  and never running untested policies at full speed.

---

## 10. Monorepo layout

```
benchtop-lab/
├── packages/
│   ├── benchtop-core/         # compat layer (only LeRobot import surface), shared models, logging (import: benchtop_core)
│   ├── benchtop-sim/          # MuJoCo tasks, scenes, assets, experts, EnvHub export   (import: benchtop_sim)
│   ├── benchtop-grade/        # rubrics, runner, stats, taxonomy, reports                (import: benchtop_grade)
│   ├── benchtop-data/         # dataset doctor                                          (import: benchtop_data)
│   ├── benchtop-real/         # hardware tools: calib-check, real eval protocol         (import: benchtop_real)
│   └── benchtop-lab/          # meta-package + `benchtop` CLI (Typer) + doctor          (import: benchtop_lab)
├── projects/                  # p0_setup … p8_real_capstone (see §5.2)
├── envhub/                    # generated EnvHub folders, one per task (from benchtop-sim)
├── docs/                      # MkDocs site source + planning docs
├── notebooks/                 # shared Kaggle/Colab helpers
├── hardware/                  # grid mat SVG/PDF, camera mount notes
├── tools/                     # repo maintenance scripts (release, envhub export, link check)
├── tests/                     # cross-package integration and end-to-end tests
├── .github/                   # CI workflows, issue/PR templates
├── .claude/                   # Claude Code agents, commands, skills
├── pyproject.toml             # uv workspace root
├── uv.lock
├── CLAUDE.md, README.md, CONTRIBUTING.md, CODE_OF_CONDUCT.md, LICENSE, LICENSE-CONTENT, NOTICE
```

Package dependency direction (enforced by import-linter contracts):
`benchtop-lab (CLI)` → `benchtop-grade`, `benchtop-data`, `benchtop-real` → `benchtop-core` and `benchtop-sim`.
`benchtop-sim` depends on no other Benchtop package and never imports `lerobot` or `torch`.
Only `benchtop_core.compat` imports `lerobot`.

---

## 11. Tech stack and tooling

| Area | Choice | Why |
| --- | --- | --- |
| Language | Python 3.12 (3.13 tested in CI) | LeRobot requires ≥ 3.12 |
| Packaging | **uv** workspace, hatchling backend, `uv.lock` committed | Fast, reproducible, multi-package |
| Simulation | MuJoCo 4.0.x, Menagerie SO-101 | Laptop CPU, Apache-2.0, matches official Space |
| IK | mink 1.4.x | Maintained, Apache-2.0, MuJoCo-native |
| Robot learning | LeRobot 0.7.x (`lerobot[training]` extras as needed) | The ecosystem standard |
| CLI | Typer + Rich | Discoverable, typed |
| Config | Pydantic v2 models + YAML (rubrics, suites) | Validation and JSON Schema export |
| Plots | matplotlib | Pure-pip, CPU |
| Lint/format | ruff (lint + format) | One tool |
| Types | mypy (strict on our packages) | LeRobot itself is now fully typed |
| Tests | pytest, pytest-xdist, hypothesis, pytest-cov, syrupy (snapshot reports) | Speed + coverage |
| Architecture rules | import-linter | Enforce dependency direction |
| Hooks | pre-commit (ruff, a local `uv run mypy` hook, trailing whitespace, large-file guard, gitleaks secret scan) | Catch issues before CI |
| CI | GitHub Actions (free for public repos) | See §12 |
| Docs | MkDocs Material 9.x (feature-frozen since Nov 2025, fixes until May 2027) or its successor Zensical; decided by ADR in S04. mkdocstrings for API docs; `mike` if versioned docs are needed | Free, searchable, GitHub Pages |
| Licenses | `reuse` lint with `REUSE.toml` + `LICENSES/` for files that cannot carry headers; `pip-licenses` allowlist check | Keep the project clean |
| Video | PyAV (BSD-3; its wheels bundle LGPL FFmpeg, which we do not vendor) and opencv-python-headless (Apache-2.0) for doctor vision checks | Pure-pip, CPU |
| Releases | One shared version in the root, `tools/bump_version.py`, CHANGELOG generated with git-cliff from Conventional Commits; tags and GitHub releases created only with the owner's approval; PyPI Trusted Publishing later (needs D4) | No tokens in CI |
| PyTorch wheels | uv extras `cpu` and `cu` declared as conflicting, each mapped to its PyTorch index via `[tool.uv.sources]`; CI uses `cpu` | Small installs on laptops and CI, CUDA where wanted |

Torch on CI: CPU wheels via the `cpu` extra to keep runners light; GPU paths are exercised in notebooks only.
`benchtop_core` imports `compat` lazily so that `benchtop --help` and sim-only commands start fast.

---

## 12. Testing strategy

| Layer | What | Where / when |
| --- | --- | --- |
| Unit | Success checks (positive + adversarial), seeds/splits, stats (Wilson vs reference values), rubric parsing, doctor checks on synthetic datasets, CLI argument parsing | Every push, < 3 min |
| Property | Hypothesis: FK/IK round-trips, Wilson bounds monotonic, seed splits disjoint | Every push |
| Contract | Our envs satisfy LeRobot's env contract (load through `make_env`, run through LeRobot's sim robot and a 2-episode `lerobot-eval`), observation dtypes/shapes, `LEROBOT_SIM` keys | Every push (CPU, tiny images) |
| Determinism | Same seed → identical observations and outcomes | Every push |
| Golden | Scripted experts' success rates on fixed seeds; tiny reference checkpoints' outcomes | Every push (short), nightly (full) |
| Snapshot | Report Markdown/HTML snapshots | Every push |
| Integration | `benchtop demo → lerobot-train (few steps) → benchtop grade` end to end on CPU | Nightly + before release |
| Docs | `mkdocs build --strict`, link check, notebook execution of CPU notebooks | Every push (build), nightly (links, notebooks) |
| Platform | Linux (ubuntu-latest), macOS (arm64); Windows via WSL documented | PRs: Linux; nightly: matrix |
| Performance | Step/render throughput benchmarks with regression thresholds | Nightly |

Rules: coverage ≥ 85% on `benchtop_*` packages (excluding hardware I/O), enforced with `--cov-fail-under=85` in CI;
no network in unit tests (Hub calls mocked); `MUJOCO_GL=egl` in CI with `libegl1 libegl-mesa0 libgl1-mesa-dri
libosmesa6`; `render` tests run in their own CI job and are skipped by default on machines without GL.

---

## 13. Docs site

- Built with MkDocs Material, published to GitHub Pages from `main` (free).
- Sections: Start here, Projects (P0 to P8), Concepts (short primers linked from lessons), Guides (Kaggle/Colab,
  hardware, troubleshooting), Reference (CLI, Python API, rubric schema, results schema), Contributing.
- Every lesson page has: objectives, time/compute box, predict-run-explain blocks, "common failures", rubric table,
  and an "edit on GitHub" link.
- Content license CC BY 4.0 stated in the footer.

---

## 14. Licensing

| Asset | License | Notes |
| --- | --- | --- |
| Code in `packages/`, `tools/`, `projects/*/starter`, `projects/*/solution`, tests | Apache-2.0 | Matches LeRobot, MuJoCo, Menagerie, mink; includes a patent grant |
| Lessons, docs, figures, quizzes | CC BY 4.0 | Instructors may reuse with attribution |
| Datasets and checkpoints we publish | CC BY 4.0 (datasets), Apache-2.0 (checkpoints) | Stated on each Hub card |
| Vendored SO-101 model | Apache-2.0 (Menagerie/TheRobotStudio) | Keep upstream LICENSE + NOTICE entry |
| SmolVLA base weights (used, not redistributed) | Apache-2.0 | P6 |
| π0/π0.5 weights | Gemma license | Not used in graded projects |

Compatibility: Apache-2.0 code may depend on MIT (Gymnasium), BSD (PyTorch) and Apache-2.0 components. CC BY 4.0 applies
only to non-code content. SPDX headers on every source file; `reuse lint` in CI.

---

## 15. Community and contribution plan

- **Good first issues** labelled from day one: new perturbations, doctor checks, clinic cases, translations of lessons.
- **Contribution types:** tasks (with success checks and tests), clinic cases, doctor checks, lesson fixes, notebooks.
- **Governance:** a single maintainer for v1, with CODEOWNERS; RFCs as GitHub Discussions for new projects or tasks.
- **Support:** GitHub Discussions (Q&A, Show and tell with report cards); issue templates for bug, task proposal,
  lesson feedback.
- **Recognition:** all-contributors table; a "Report card gallery" docs page for learners who opt in via PR.
- **Upstream citizenship:** fixes found in LeRobot are drafted as patches with a write-up; the owner opens upstream
  issues/PRs himself (the build agent never posts outside this repository). We never fork LeRobot.

---

## 16. Launch plan (open-source launch; all posts are drafts for Shiva's approval)

| When | Action |
| --- | --- |
| v0.1 (after M4) | Soft launch: share the sim suite + grader in LeRobot Discord `#showcase` and HF forum as "feedback wanted". Draft only. |
| v1.0 day | Show HN ("Show HN: Benchtop Lab – free graded robot-learning projects for the SO-101"), r/robotics, r/MachineLearning (weekend "Project" thread), r/ROS, X thread with a demo GIF and a report card, LeRobot Discord, HF community blog post. |
| Week +1 | Technical post: "Why your ACT policy looks good and still fails" with measured numbers from P3/P4/P7. |
| Week +2 | Instructor outreach: robotics clubs and electives (India and US), offering the free 6-week module. |
| Ongoing | Answer LeRobot issues and forum threads where the doctor or clinic genuinely helps; no link spam. |

Assets prepared before launch: 30-second demo GIF, report-card screenshot, one-command quickstart verified on a fresh
machine, FAQ, and launch post drafts in `docs/launch/drafts/` (drafts only; nothing is posted without Shiva's approval).

---

## 17. Success metrics

| Horizon | Metric | Target |
| --- | --- | --- |
| Launch + 4 weeks | GitHub stars | 300 |
| Launch + 4 weeks | Learners completing P3 (opt-in report-card PRs or Discussions posts) | 25 |
| Launch + 3 months | Stars / forks | 1,000 / 100 |
| Launch + 3 months | External contributors | 10 |
| Launch + 3 months | Courses or clubs using it | 2 |
| Always | CI green on `main` | 100% of commits |
| Always | Fresh-machine quickstart time | < 10 min to first graded result |

v2 candidates, prioritized by community demand: RL track (HIL-SERL in sim), public leaderboard Space, bimanual SO-101,
LeKiwi, more VLA projects, translations.

---

## 18. Risks and open decisions

### 18.1 Risks

| Risk | Likelihood | Impact | Mitigation |
| --- | --- | --- | --- |
| LeRobot breaking changes (every minor release) | High | High | Pin `0.7.*`; one compat module; contract tests; a scheduled "upstream canary" CI job against LeRobot `main` |
| Official SO-101 Space or HF course grows to cover the same ground | Medium | Medium | Stay complementary (grading, diagnostics, progression); cross-evaluate on the official env; contribute upstream |
| Sim physics of grasping is unrealistic | Medium | Medium | Use Menagerie's tuned collision params; contact-gated checks; document the sim-to-real gap honestly in P8 |
| CPU training too slow for P3 | Medium | High | State-based policies by design; measure in M6; shrink task or model if needed |
| GPU reference results need an account (Kaggle/Colab) | High | Medium | Open decision D2; otherwise publish GPU thresholds as provisional with community verification |
| Claude usage limits slow the build | High | Medium | Sessions sized for ~60% of a 5-hour window, weekly cap guard, resumable progress log |
| Learner installs fail on diverse machines | Medium | High | `benchtop doctor`, nightly macOS/Linux matrix, Docker image, Colab fallback |

### 18.2 Open decisions for Shiva

- **D1. Name.** "Benchtop Lab" (repo `benchtop-lab`, PyPI `benchtop-lab` and CLI `benchtop`, all free on 23 Nov 2026).
  Note: an unrelated PyPI package named `benchtop` exists, so the import names are `benchtop_*`, not `benchtop`.
- **D2. Free GPU account for reference runs.** P4 to P6 reference results need a GPU. Option: Shiva creates a free
  Kaggle account (phone-verified) and lets the build use its 30 h/week; otherwise GPU thresholds stay provisional.
- **D3. Hugging Face account/org** to publish EnvHub Spaces, reference datasets and checkpoints (free).
- **D4. PyPI publishing** via Trusted Publishing (free account needed for `benchtop-lab`).
- **D5. Real hardware.** Does Shiva have (or plan to get) an SO-101? P8 can ship with a protocol validated by the
  community, but a maintainer-run real result would make it far stronger.
- **D6. Conduct/security contact** email for CODE_OF_CONDUCT and SECURITY (GitHub private reporting is used meanwhile).
- **D7. Build-machine guardrails.** Allow branch protection on `main` (CI required, no force-push) and drop the
  `delete_repo` scope that was added to the build machine's GitHub login for the earlier test-repo cleanup.
