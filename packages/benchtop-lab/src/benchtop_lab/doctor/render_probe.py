# SPDX-FileCopyrightText: 2026 Benchtop Lab contributors
# SPDX-License-Identifier: Apache-2.0
"""Render a 64 by 64 MuJoCo test scene offscreen and print what came out as one line of JSON.

`benchtop doctor` runs this module in a child process (`python -m benchtop_lab.doctor.render_probe`): a missing
or broken OpenGL backend can abort the interpreter instead of raising, and `MUJOCO_GL` is read once at import.
"""

import json
import sys
from typing import Final

SIZE: Final = 64

SCENE: Final = f"""
<mujoco model="benchtop-doctor">
  <visual><global offwidth="{SIZE}" offheight="{SIZE}"/></visual>
  <worldbody>
    <light pos="0 0 2"/>
    <geom type="plane" size="1 1 0.1" rgba="0.8 0.8 0.8 1"/>
    <geom type="box" size="0.1 0.1 0.1" pos="0 0 0.1" rgba="0.1 0.4 0.8 1"/>
    <camera name="probe" pos="0 -1 0.5" xyaxes="1 0 0 0 0.5 1"/>
  </worldbody>
</mujoco>
"""


def render_test_scene() -> dict[str, object]:
    """Render the test scene with the backend selected by `MUJOCO_GL`.

    Returns:
        The image `shape`, its `dtype` and the number of distinct pixel `colours` (1 means a blank image).
    """
    import mujoco  # noqa: PLC0415  (imported here so an import failure is reported by `main`)
    import numpy as np  # noqa: PLC0415

    model = mujoco.MjModel.from_xml_string(SCENE)
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    renderer = mujoco.Renderer(model, SIZE, SIZE)
    try:
        renderer.update_scene(data, camera="probe")
        image = renderer.render()
    finally:
        renderer.close()
    colours = len(np.unique(image.reshape(-1, image.shape[-1]), axis=0))
    return {"shape": list(image.shape), "dtype": str(image.dtype), "colours": int(colours)}


def main() -> int:
    """Print the probe result as JSON; exit 0 when a non-blank image of the right shape was rendered."""
    try:
        result = render_test_scene()
    except Exception as error:  # noqa: BLE001  (any failure of any GL backend is the finding)
        print(json.dumps({"ok": False, "error": f"{type(error).__name__}: {error}".splitlines()[0]}))
        return 1
    ok = result["shape"] == [SIZE, SIZE, 3] and result["dtype"] == "uint8" and result["colours"] != 1
    print(json.dumps({"ok": ok, **result}))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
