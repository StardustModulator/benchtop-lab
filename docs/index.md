---
title: Benchtop Lab
description: Graded, sim-first robot-learning projects for the SO-101 arm, built on LeRobot and MuJoCo.
hide:
  - navigation
  - toc
---

<!-- SPDX-License-Identifier: CC-BY-4.0 -->

<div class="hero" markdown>

Free and open source · SO-101 · LeRobot 0.7 · MuJoCo
{ .eyebrow }

# Learn robot learning by measuring it

Benchtop Lab is a sequence of graded, simulation-first projects for the SO-101 arm. You build a policy, an
auto-grader tests it on scenes it has never seen, and you leave with numbers you can defend. No robot is needed
to start.
{ .lead }

<div class="actions" markdown>
[Start here](start/index.md){ .md-button .md-button--primary }
[See the nine projects](projects/index.md){ .md-button }
</div>

</div>

!!! info "Status: under construction"

    The project is being built in the open, milestone by milestone. Today the repository installs, the
    `benchtop` command runs, and this site exists. The simulator, the grader and the lessons arrive in later
    milestones. [Progress](PROGRESS.md) records what is done, and nothing on this site describes a feature as
    available before it is.

## Why it exists

> Training loss went down. The robot still misses the cube.

Tools for *training* a robot policy are excellent. What is hard to find is a path that teaches you *why* a policy
works or fails, and an honest way to *measure* it. Tutorials tend to end at the training command. Few tell you
whether 7 successes out of 10 is good, lucky or meaningless (it is consistent with a true success rate anywhere
from 40% to 89%; see [the Wilson score interval](concepts/wilson-interval.md)).

## What you will work with

<div class="grid cards" markdown>

-   **A task suite in simulation**

    ---

    MuJoCo tasks for the SO-101 with seeded randomisation and held-out exam seeds. Joint names, units and control
    rate match LeRobot's SO-101 follower, so the same code path can drive a real arm.

    Planned for milestones M1 and M2

-   **A grader**

    ---

    Runs your policy on held-out scenes and robustness suites, reports success with 95% confidence intervals,
    and writes a report card you can put in a portfolio.

    Planned for milestone M4

-   **A dataset doctor**

    ---

    Checks a LeRobot dataset for the problems that quietly ruin policies: idle frames, timestamp gaps, mixed
    strategies, thin workspace coverage. Every finding comes with a fix.

    Planned for milestone M5

-   **Nine graded projects**

    ---

    From setup and kinematics to behaviour cloning, vision policies, multimodal demonstrations, a small
    vision-language-action model, a debugging clinic and an optional real-arm capstone.

    [Project list](projects/index.md)

</div>

## Principles

1. **Measure honestly.** Held-out seeds, confidence intervals and robustness suites, never a single lucky video.
2. **Simulation first, real-arm ready.** The same joint names, units and 30&nbsp;fps control rate as LeRobot's SO-101
   follower.
3. **Build on LeRobot, do not fork it.** Its datasets, policies and training stay as they are. Benchtop Lab adds
   the curriculum, the grading and the diagnostics.
4. **Runs on a laptop.** Five of the nine projects need only a CPU. The vision projects fit free cloud GPUs.
5. **Free forever.** Code is Apache-2.0 and lessons are CC&nbsp;BY&nbsp;4.0. There is no paid tier.

## Where to go next

| If you want to… | Read |
| --- | --- |
| Install the repository and run the command line | [Install from source](start/install.md) |
| Learn the joint names, units and camera names used everywhere | [SO-101 conventions](start/conventions.md) |
| See what each project teaches and how it is graded | [Projects](projects/index.md) |
| Follow the build or review the design | [Project](project/index.md) |
| Help out | [Contributing](contributing/index.md) |
