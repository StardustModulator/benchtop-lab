<!-- SPDX-FileCopyrightText: 2026 Benchtop Lab contributors -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# benchtop-sim

MuJoCo tasks, scenes, success checks, perturbations and scripted experts for the SO-101 arm.

Part of [Benchtop Lab](https://github.com/StardustModulator/benchtop-lab). Import name: `benchtop_sim`.
This package is released together with the other Benchtop Lab packages under one shared version.

Code is licensed under Apache-2.0.

## What is here so far

```python
import mujoco
from benchtop_sim import ObjectSpec, SceneSpec, lerobot_to_ctrl

cube = ObjectSpec("cube", "box", (0.015, 0.015, 0.015), pos=(0.25, 0.0, 0.015))
model = SceneSpec(objects=(cube,)).build()  # SO-101 on a table, cameras "front" and "wrist"
data = mujoco.MjData(model)
data.ctrl[:] = lerobot_to_ctrl([0, -60, 60, 35, 0, 30])  # degrees, gripper 0 (closed) to 100 (open)
mujoco.mj_step(model, data, nstep=200)
```

- `benchtop_sim.so101`: joint order, `<joint>.pos` names and the joint limits table.
- `benchtop_sim.units`: the one conversion between LeRobot units and MuJoCo actuator targets.
- `benchtop_sim.scene` and `benchtop_sim.builder`: scene description dataclasses and the `mujoco.MjSpec` builder.

The world origin is on the table top (`z = 0` is the surface); the arm sits at the origin and reaches towards `+x`.

## Third-party model

`src/benchtop_sim/assets/robotstudio_so101/` is an unmodified copy of the SO-101 model from
[MuJoCo Menagerie](https://github.com/google-deepmind/mujoco_menagerie/tree/main/robotstudio_so101)
(Apache-2.0, derived from TheRobotStudio's SO-ARM100). Its `LICENSE` and our `UPSTREAM.md` (pinned commit,
derivation, checksums) are in that directory.
