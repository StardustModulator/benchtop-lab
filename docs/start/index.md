---
title: Start here
description: What Benchtop Lab is, who it is for, and what works today.
---

<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Start here

Benchtop Lab teaches robot learning through nine graded projects on the SO-101, a low-cost six-joint arm. Each
project has learning objectives, starter code and an auto-grader. The work happens in simulation first, so you
can begin without hardware.
{ .lead }

## Who it is for

- **Machine-learning and software engineers moving into robotics**, who know PyTorch but not joint spaces,
  calibration or action chunking.
- **Robotics students** who want a measured project beyond coursework.
- **SO-101 owners** who built the kit and cannot get a policy to work reliably.
- **Instructors and clubs** who want a free lab sequence with automatic grading.

You need Python and basic PyTorch. You do not need a robot, a GPU or earlier robotics experience.

## What works today

The project is in its first milestone (M0, foundations). This table is the honest state of each piece.

| Piece | State | Arrives in |
| --- | --- | --- |
| Repository, packaging, quality gate and continuous integration | Available | M0 |
| `benchtop` command line (`--version`, `--help`) | Available | M0 |
| This documentation site | Available | M0 |
| `benchtop doctor` (checks your machine) | Planned | M0 |
| SO-101 simulation and the first task | Planned | M1 |
| Full task suite | Planned | M2 |
| Scripted experts, teleoperation, demonstration data | Planned | M3 |
| Grader and report cards | Planned | M4 |
| Dataset doctor | Planned | M5 |
| Projects P0–P8 (lessons, starter code, rubrics) | Planned | M7–M9 |

The [milestone plan](../MILESTONES.md) has the full schedule, and [Progress](../PROGRESS.md) is updated after
every build session.

## Your first ten minutes

1. [Install the repository from source](install.md) and run `benchtop --version`.
2. Read the [SO-101 conventions](conventions.md). Every dataset, policy and task on this site uses them.
3. Skim the [project list](../projects/index.md) to see where the course is heading.
