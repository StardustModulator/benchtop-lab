---
title: SO-101 conventions
description: Joint names and order, units, control rate, camera names and observation layout used across Benchtop Lab.
---

<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# SO-101 conventions

Every task, dataset, policy and grader in Benchtop Lab uses one set of conventions. They match LeRobot's SO-101
follower, so what you learn in simulation carries over to the real arm without renaming or rescaling anything.
{ .lead }

## Joints

The arm has six joints. Their order never changes.

| Index | Joint | Feature name | Unit |
| ---: | --- | --- | --- |
| 0 | Shoulder pan | `shoulder_pan.pos` | degrees |
| 1 | Shoulder lift | `shoulder_lift.pos` | degrees |
| 2 | Elbow flex | `elbow_flex.pos` | degrees |
| 3 | Wrist flex | `wrist_flex.pos` | degrees |
| 4 | Wrist roll | `wrist_roll.pos` | degrees |
| 5 | Gripper | `gripper.pos` | 0 (closed) to 100 (open) |

Arm joints are measured in degrees with zero at the middle of each joint's range. The gripper is a percentage of
its opening, not an angle.

## Control

- An **action** is six absolute joint position targets, in the order and units above.
- The control rate is **30&nbsp;fps**: the policy is asked for one action every 1/30 of a second.

## Observations

| Key | Type | Meaning |
| --- | --- | --- |
| `pixels` | dictionary of images (height × width × 3, 8-bit) | One image per camera |
| `agent_pos` | 6 numbers (32-bit float) | Current joint positions |
| `environment_state` | numbers (32-bit float), optional | Simulator state for state-based policies |

There are two cameras, named `front` and `wrist`.

## Episodes and success

An episode ends on the first step where the task's full success condition holds. The environment reports
`is_success` on every step, so a grader never has to guess from the last frame.

!!! note "Why fixed conventions matter"

    A policy trained on degrees and evaluated on radians fails without an error message. A dataset whose
    gripper runs 0–1 instead of 0–100 trains a policy that barely opens its hand. Fixing the conventions once
    removes a whole class of silent failures; the debugging clinic (P7) teaches how to spot the rest.
