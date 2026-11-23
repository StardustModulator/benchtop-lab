---
title: Projects
description: The nine graded Benchtop Lab projects, what each teaches and how it is graded.
---

<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Projects

Nine projects, each with a written lesson, starter code, exercises and a rubric. Every project ends with a
report card: a success rate with a confidence interval, a robustness profile and a gallery of failures.
{ .lead }

!!! info "Planned for milestones M7–M9"

    The lessons are not written yet. The table is the plan they will follow; thresholds and compute estimates
    are confirmed only once reference policies have been trained and measured (milestone M6).

| # | Project | You learn | Graded on | Compute |
| --- | --- | --- | --- | --- |
| P0 | Setup and tour | The SO-101, LeRobot conventions, simulated robots | Doctor passes, valid teleoperation dataset, tour quiz | Any laptop |
| P1 | Kinematics and a scripted expert | Joint space and task space, inverse kinematics, why classical control is brittle | Reach error, scripted pick success | CPU |
| P2 | Demonstrations that teach | LeRobotDataset v3, teleoperation, coverage, data quality | Dataset quality gate | CPU |
| P3 | Your first policy | Behaviour cloning, compounding error, action chunking (ACT) | Held-out success, lower confidence bound | CPU |
| P4 | Seeing is believing | Vision policies, augmentation, robustness | Nominal and perturbation suites | GPU or free cloud |
| P5 | When averaging fails | Multimodal demonstrations, Diffusion Policy and ACT | Success and mode coverage | GPU or free cloud |
| P6 | Language in the loop | Fine-tuning a small vision-language-action model (SmolVLA) | Success per instruction | GPU or free cloud |
| P7 | Debugging clinic | Diagnosing broken data, calibration, cameras, normalisation | Correct diagnosis and a fixed policy | CPU |
| P8 | Real arm capstone (optional) | Calibration, sim-to-real transfer, honest real-world evaluation | Standard real-robot protocol | Your SO-101 |

## How grading works

Each project has four grades: Fail, Pass, Merit and Distinction. A threshold is compared with the **lower bound
of the 95% [Wilson score interval](../concepts/wilson-interval.md)** on held-out exam seeds, not with the raw
success rate, so a lucky run of ten episodes cannot earn a grade. The full specification is in the
[plan](../PLAN.md).
