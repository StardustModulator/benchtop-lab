---
name: mujoco-env-authoring
description: Conventions for writing Benchtop Lab MuJoCo tasks, success checks, perturbations and scripted experts for the SO-101. Use when working in packages/benchtop-sim.
---

# Authoring tasks in benchtop-sim

## Building scenes
- Use `mujoco.MjSpec` to compose the vendored Menagerie `robotstudio_so101` with task objects. Never string-template XML.
- Keep the Menagerie collision parameters for the gripper; they were tuned for manipulation.
- Cameras: `front` (scene) and `wrist` (gripper mount). Default image 128×128 for CPU projects; 480×640 optional.
- Physics substeps: `substeps = max(1, round(1 / (fps * timestep)))`, then set `timestep = 1 / (fps * substeps)`.

## Units and control
- Actions are absolute targets: degrees for 5 arm joints, gripper 0 (closed)–100 (open). Convert with the single tested
  function in `benchtop_sim.units`; experts use the same function.

## Randomness
- `SeedSequence(seed).spawn(k)` into separate generators for objects, joints, camera, perturbation, task-language.
  Adding a perturbation must not change object placement for the same seed (tested).

## Success checks (must be unfakeable)
- Grasp: both jaws in contact and object above the table.
- Placement: in region, below height threshold, speed < 1 cm/s for N consecutive steps, not touching the gripper.
- Hold: state maintained for the hold duration, not passed through.
- Write positive and adversarial tests with constructed MuJoCo states (set `qpos`/`qvel`, `mj_forward`).

## Stages and metrics
- Every task defines ordered stages; `info["stage"]` is the furthest stage reached; metrics per PLAN §6.5.

## Experts
- FSM over Cartesian waypoints solved with IK; smooth joint interpolation; gripper commands as 0–100.
- Target ≥ 95% success on 200 seeds; log failing seeds and keep them as regression tests.

## Performance
- No allocations in the step loop beyond observation arrays; reuse `MjData`; render only requested cameras.
