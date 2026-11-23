<!--
SPDX-FileCopyrightText: 2026 Benchtop Lab contributors
SPDX-License-Identifier: CC-BY-4.0
-->
# Upstream record: `robotstudio_so101`

This directory is an unmodified copy of the SO-101 model from MuJoCo Menagerie. Benchtop Lab added only this
file and `SHA256SUMS`.

| | |
| --- | --- |
| Source | <https://github.com/google-deepmind/mujoco_menagerie/tree/main/robotstudio_so101> |
| Pinned commit | `370c43965323c0944b433b202aac5058b5f907a9` (Menagerie `main`, committed 2026-11-10) |
| Last upstream change to this model | `3abca2e302625cec9429c49806121ea2855cef81` (2026-09-28, "Fix SO101 wrist_roll joint range upper limit") |
| Vendored on | 2026-11-23 (session S05) |
| Licence | Apache-2.0, see [LICENSE](LICENSE) (copied byte for byte) |
| Requires | MuJoCo 3.1.3 or later (Benchtop Lab pins 4.0.x) |

## Derivation

1. TheRobotStudio published the SO-101 as `Simulation/SO101/so101_new_calib.xml` in
   [SO-ARM100](https://github.com/TheRobotStudio/SO-ARM100) (Apache-2.0), commit
   `aec17bbc256d1a7342d53aaa4950595d4c30b40d`. "New calibration" means every joint reads zero at mid-range.
2. MuJoCo Menagerie derived `robotstudio_so101` from it. Their steps are listed in [README.md](README.md):
   rounded floats, the `implicitfast` integrator, the default actuator force range, primitive collision
   geometry, tuned gripper contact parameters, and a camera mount with the `wrist_cam` camera.
3. Benchtop Lab copies that directory at the pinned commit **without edits**. Everything we change (mounting
   the arm on a table, renaming `wrist_cam` to `wrist`, adding cameras, lights and objects) happens in memory in
   `benchtop_sim.builder` through `mujoco.MjSpec`.

## What was copied

- `so101.xml`, `LICENSE`, `README.md`, `CHANGELOG.md` and all 19 meshes in `assets/`.
- Not copied: `scene.xml` and `scene_box.xml` (upstream demo scenes; ours are built in code) and `so101.png`
  (a 1 MB preview image, so the image link in upstream's README is dead in this copy).

The official LeRobot Space `lerobot/so101-tabletop-mujoco` bundles the same model at Menagerie commit
`0059d4335f8156206f63a35662313385f7ad6d74`.

## Integrity

`SHA256SUMS` lists the SHA-256 digest of every copied file. `packages/benchtop-sim/tests/test_so101_model.py`
recomputes them, so an accidental edit of a vendored file fails the gate. Check by hand with:

```bash
cd packages/benchtop-sim/src/benchtop_sim/assets/robotstudio_so101 && sha256sum --check SHA256SUMS
```

## Updating

1. Check out the new Menagerie commit and copy the same files over this directory.
2. Regenerate the digests (`sha256sum CHANGELOG.md LICENSE README.md so101.xml assets/*.stl > SHA256SUMS`),
   update the commit and dates above and in `NOTICE`, and update the joint limits table in
   `benchtop_sim/so101.py` if any actuator `ctrlrange` changed.
3. Run the full gate including `-m render`. The parity tests in `test_builder.py` and the limits test in
   `test_so101_model.py` show what moved. Record the update in `docs/PROGRESS.md`.
