<div align="center">

# Benchtop Lab

**Learn robot learning by doing. Graded, sim-first projects for the SO-101 arm, built on LeRobot and MuJoCo.**

From "I installed LeRobot" to "my policy works, and here are the numbers that prove it."
No robot required to start. 100% open source. Nothing is paid, ever.

[![CI](https://github.com/StardustModulator/benchtop-lab/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/StardustModulator/benchtop-lab/actions/workflows/ci.yml?query=branch%3Amain)
[![Nightly](https://github.com/StardustModulator/benchtop-lab/actions/workflows/nightly.yml/badge.svg?branch=main)](https://github.com/StardustModulator/benchtop-lab/actions/workflows/nightly.yml)
[![License: Apache-2.0](https://img.shields.io/badge/code-Apache--2.0-blue.svg)](LICENSE)
[![Content: CC BY 4.0](https://img.shields.io/badge/content-CC%20BY%204.0-lightgrey.svg)](LICENSE-CONTENT)
![Status: planning](https://img.shields.io/badge/status-planning-orange.svg)

</div>

> **Status (23 Nov 2026): planning.** This repository currently holds the full specification and build plan.
> Code lands milestone by milestone; follow [docs/PROGRESS.md](docs/PROGRESS.md) for what is done and what is next.

---

## Why this exists

Robot learning is having its moment. LeRobot has about 29,000 GitHub stars, the SO-101 arm costs a few hundred dollars,
and thousands of people have joined LeRobot hackathons. Yet the most common story from learners is the same:

> *"Training loss went down. The robot still misses the cube."*

The tooling to **train** a policy is excellent. What is missing is a path that teaches you **why** a policy works or fails,
and a way to **measure** it honestly:

- Tutorials end at "run `lerobot-train`". Few tell you whether 7 out of 10 successes is good, lucky, or meaningless.
- Most failures are data and setup problems (calibration drift, a moved camera, two grasping styles averaged into one,
  thin coverage of the workspace), not model problems. Nobody teaches you to diagnose them.
- Without hardware you cannot practise at all, and with hardware every mistake costs an afternoon of re-recording.
- Free courses explain concepts; paid cohorts cost $1,800 or more. There is very little in between that makes you *build*.

**Benchtop Lab** fills that gap with a sequence of hands-on projects. Each one has clear learning objectives,
a starter kit, and an **auto-grader** that evaluates your result on held-out scenes, reports success with confidence
intervals, stress-tests robustness, and produces a report card you can put in a portfolio.

## Who it is for

- **ML and software engineers moving into robotics**, who know PyTorch but not joint spaces, calibration or action chunking.
- **Robotics students** (BS/MS) who need a credible, measured project beyond coursework.
- **SO-101 owners** who built the kit and cannot get a policy to work reliably.
- **Instructors and clubs** who want a free, ready-made lab sequence with automatic grading.

You need Python and basic PyTorch. You do not need a robot, a GPU, or any prior robotics.

## What you get

| Piece | What it does |
| --- | --- |
| **`benchtop-sim`** | A MuJoCo task suite for the SO-101: reach, push, pick-and-lift, pick-and-place, language-conditioned sorting, stacking, and a deliberately *multimodal* task. Seeded randomization, held-out exam seeds, perturbation suites, and contact-gated success checks that cannot be faked. Same observation and action interface and units as LeRobot's `so_follower`, so the same code path runs in sim and on the real arm (the sim-to-real gap still applies; P8 teaches how to measure it). Exported as self-contained LeRobot EnvHub environments. |
| **`benchtop-grade`** | The grader. Runs your policy on held-out seeds and robustness suites, reports success with 95% Wilson intervals, per-stage breakdowns (reach, grasp, transport, place), failure taxonomy and a failure-video gallery, then writes a reproducible `results.json` and a portfolio-ready report card. |
| **`benchtop-data`** | The dataset doctor. Checks a LeRobotDataset for the problems that silently ruin policies: idle frames, timestamp gaps, gripper chatter, mixed strategies, poor workspace coverage, camera drift, calibration offsets. Every finding comes with a fix. |
| **`benchtop` CLI** | One command line for everything: `benchtop doctor`, `benchtop envs`, `benchtop demo`, `benchtop teleop`, `benchtop grade`, `benchtop report`, `benchtop data check`, `benchtop clinic`, `benchtop real`. |
| **The projects** | Nine graded projects (P0 to P8) with written lessons, starter code, exercises and rubrics, published as a free docs site. |
| **The hardware path** | For SO-101 owners: a calibration checker, sim-twin teleoperation with your real leader arm, and a standard real-robot evaluation protocol with a printable grid mat. |

## The projects

| # | Project | You learn | Graded on | Compute |
| --- | --- | --- | --- | --- |
| P0 | **Setup and tour** | The SO-101, LeRobot conventions, sim robots | Doctor passes, valid teleop dataset, tour quiz | Any laptop |
| P1 | **Kinematics and a scripted expert** | Joint vs task space, IK, why classical control is brittle | Reach error, scripted pick success | CPU |
| P2 | **Demonstrations that teach** | LeRobotDataset v3, teleop, coverage, data quality | Dataset quality gate | CPU |
| P3 | **Your first policy** | Behavior cloning, compounding error, action chunking (ACT) | Held-out success, CI lower bound | CPU (state-based) |
| P4 | **Seeing is believing** | Vision policies, augmentation, robustness | Nominal + perturbation suites | GPU or free Colab/Kaggle |
| P5 | **When averaging fails** | Multimodal demos, Diffusion Policy vs ACT | Success and mode coverage | GPU or free cloud |
| P6 | **Language in the loop** | Fine-tuning a small VLA (SmolVLA) for instruction following | Per-instruction success | GPU or free cloud |
| P7 | **Debugging clinic** | Diagnosing broken data, calibration, cameras, normalization | Correct diagnosis + fixed policy | CPU |
| P8 | **Real arm capstone** (optional) | Calibration, sim-to-real, honest real-world evaluation | Standard real-robot protocol | Your SO-101 |

Every project ends with a report card: success rate with a confidence interval, robustness profile, failure gallery,
and a short write-up template. That is the artifact you show people.

## Quickstart

> Arrives with milestone M4 (the grader). The intended experience:

```bash
# Python 3.12+, Linux or macOS (Windows via WSL2)
uv tool install "benchtop-lab[cpu]"   # CPU-only PyTorch keeps the download small; drop [cpu] on a CUDA machine
benchtop doctor                       # checks Python, MuJoCo rendering, LeRobot, disk, GPU (optional)
benchtop demo pick_place --episodes 100 --out data/pick_place_scripted
lerobot-train --config_path projects/p3_first_policy/configs/act_state.json \
  --dataset.root data/pick_place_scripted       # P3's CPU recipe (exact flags land with M6)
benchtop grade p3 --policy outputs/train/act_state/checkpoints/last/pretrained_model
benchtop report p3 --open
```

## Design principles

1. **Measure honestly.** Held-out seeds, confidence intervals, robustness suites. Never a single lucky video.
2. **Sim-first, real-ready.** Same joint names, units (degrees, gripper 0 to 100) and control rate (30 fps) as LeRobot's SO-101 follower.
3. **Build on LeRobot, do not fork it.** We use its datasets, policies, training and EnvHub. We add the curriculum, the grading and the diagnostics.
4. **Runs on a laptop.** Projects P0 to P3 and P7 run on CPU. Vision and VLA projects fit free Colab or Kaggle GPUs.
5. **Reproducible.** Pinned versions, seeded everything, environment fingerprints in every result.
6. **Free forever.** Apache-2.0 code, CC BY 4.0 content. No paid tier, no gated chapters.

## Roadmap

| Milestone | Scope |
| --- | --- |
| M0 | Monorepo, tooling, CI, docs site skeleton, LeRobot compatibility layer |
| M1 | `benchtop-sim` core: SO-101 model, scene builder, LeRobot env contract, `reach` |
| M2 | Full task suite, success checkers, perturbation suites, EnvHub export |
| M3 | Kinematics, scripted experts, teleop, demo generation |
| M4 | `benchtop-grade`: protocols, metrics, report cards |
| M5 | `benchtop-data`: dataset doctor |
| M6 | Reference baselines and training recipes |
| M7 | Projects P0 to P4 (lessons, starters, rubrics) |
| M8 | Projects P5 to P7 |
| M9 | Hardware path and P8 |
| M10 | Hardening, fresh-machine tests, v1.0.0 release |

Full detail: [docs/PLAN.md](docs/PLAN.md), [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [docs/MILESTONES.md](docs/MILESTONES.md).

## Contributing

Contributions are welcome, from typo fixes to new tasks and projects. Read [CONTRIBUTING.md](CONTRIBUTING.md) and the
[Code of Conduct](CODE_OF_CONDUCT.md).

## License

- Code: [Apache License 2.0](LICENSE).
- Lessons, docs, figures and datasets we publish: [Creative Commons Attribution 4.0](LICENSE-CONTENT).
- The SO-101 MuJoCo model comes from [MuJoCo Menagerie](https://github.com/google-deepmind/mujoco_menagerie/tree/main/robotstudio_so101)
  (Apache-2.0), derived from [TheRobotStudio/SO-ARM100](https://github.com/TheRobotStudio/SO-ARM100) (Apache-2.0). See [NOTICE](NOTICE).

## Acknowledgements

Benchtop Lab stands on [LeRobot](https://github.com/huggingface/lerobot), [MuJoCo](https://github.com/google-deepmind/mujoco),
[MuJoCo Menagerie](https://github.com/google-deepmind/mujoco_menagerie), [mink](https://github.com/kevinzakka/mink) and
[The Robot Studio's SO-ARM100](https://github.com/TheRobotStudio/SO-ARM100). It is an independent community project and is not
affiliated with or endorsed by Hugging Face, Google DeepMind or The Robot Studio.
