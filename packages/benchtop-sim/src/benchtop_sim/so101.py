# SPDX-FileCopyrightText: 2026 Benchtop Lab contributors
# SPDX-License-Identifier: Apache-2.0
"""SO-101 constants: joint names and order, the joint limits table, and the vendored model location.

Everything here follows LeRobot's `so_follower` robot with `use_degrees=True` and the official
`lerobot/so101-tabletop-mujoco` Space: six joints in a fixed order, arm joints in degrees with zero at
mid-range ("new calibration"), and the gripper as an opening from 0 (closed) to 100 (open).

The limits are the actuator control ranges of the vendored MuJoCo Menagerie model
(`assets/robotstudio_so101/so101.xml`); a test compiles the model and fails if this table drifts from it.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from importlib.resources import as_file, files
from pathlib import Path
from typing import Final

__all__ = [
    "ARM_JOINTS",
    "GRIPPER_JOINT",
    "HOME",
    "JOINTS",
    "JOINT_LIMITS",
    "JOINT_NAMES",
    "LEROBOT_SIM",
    "NUM_JOINTS",
    "UPSTREAM_WRIST_CAMERA",
    "JointLimit",
    "joint_limit",
    "so101_model_path",
]

JOINTS: Final[tuple[str, ...]] = (
    "shoulder_pan",
    "shoulder_lift",
    "elbow_flex",
    "wrist_flex",
    "wrist_roll",
    "gripper",
)
"""MuJoCo joint and actuator names, in LeRobot's order."""

NUM_JOINTS: Final[int] = len(JOINTS)
ARM_JOINTS: Final[tuple[str, ...]] = JOINTS[:5]
"""The five revolute arm joints (degrees in LeRobot units)."""
GRIPPER_JOINT: Final[str] = JOINTS[5]
"""The gripper joint (0 = closed, 100 = open in LeRobot units)."""

JOINT_NAMES: Final[tuple[str, ...]] = tuple(f"{joint}.pos" for joint in JOINTS)
"""State and action feature names as LeRobot spells them: `<joint>.pos`."""

LEROBOT_SIM: Final[dict[str, object]] = {
    "fps": 30,
    "control_mode": "position",
    "semantics": "so101-joint-degrees-v1",
    "state_names": list(JOINT_NAMES),
    "action_names": list(JOINT_NAMES),
    "robot_type": "so_follower",
}
"""How LeRobot describes this simulated robot (the official Space's key set)."""

HOME: Final[tuple[float, ...]] = (0.0, -60.0, 60.0, 35.0, 0.0, 30.0)
"""A folded pose above the table with the gripper part open, in LeRobot units (same as the official Space)."""

UPSTREAM_WRIST_CAMERA: Final[str] = "wrist_cam"
"""Name of the gripper camera inside the vendored MJCF; the scene builder renames it to `wrist`."""


@dataclass(frozen=True, slots=True)
class JointLimit:
    """Control limits of one joint, in MuJoCo units and in LeRobot units.

    Attributes:
        name: Joint (and actuator) name in the MJCF.
        ctrl_min: Lower actuator target in radians.
        ctrl_max: Upper actuator target in radians.
        unit: `"deg"` for arm joints, `"percent"` for the gripper opening.
    """

    name: str
    ctrl_min: float
    ctrl_max: float
    unit: str

    @property
    def lerobot_min(self) -> float:
        """Lower limit in LeRobot units (degrees, or 0 for the gripper)."""
        return 0.0 if self.unit == "percent" else math.degrees(self.ctrl_min)

    @property
    def lerobot_max(self) -> float:
        """Upper limit in LeRobot units (degrees, or 100 for the gripper)."""
        return 100.0 if self.unit == "percent" else math.degrees(self.ctrl_max)


JOINT_LIMITS: Final[tuple[JointLimit, ...]] = (
    JointLimit("shoulder_pan", -1.91986, 1.91986, "deg"),
    JointLimit("shoulder_lift", -1.74533, 1.74533, "deg"),
    JointLimit("elbow_flex", -1.69, 1.69, "deg"),
    JointLimit("wrist_flex", -1.65806, 1.65806, "deg"),
    JointLimit("wrist_roll", -2.74385, 2.84121, "deg"),
    JointLimit("gripper", -0.17453, 1.74533, "percent"),
)
"""Joint limits table, in `JOINTS` order (actuator `ctrlrange` of the vendored model)."""


def joint_limit(name: str) -> JointLimit:
    """Return the limits of one joint.

    Args:
        name: A joint name from `JOINTS`, with or without the `.pos` suffix.

    Raises:
        KeyError: If the name is not an SO-101 joint.
    """
    bare = name.removesuffix(".pos")
    for limit in JOINT_LIMITS:
        if limit.name == bare:
            return limit
    raise KeyError(f"Unknown SO-101 joint {name!r}. Valid joints, in order: {', '.join(JOINTS)}.")


def so101_model_path() -> Path:
    """Return the path of the vendored Menagerie `so101.xml` (its meshes sit in `assets/` next to it).

    Raises:
        FileNotFoundError: If the model is missing, which means the install is incomplete.
    """
    resource = files("benchtop_sim").joinpath("assets", "robotstudio_so101", "so101.xml")
    # benchtop-sim is always installed unpacked (wheel or editable), so the resource is a real file.
    with as_file(resource) as path:
        if not path.is_file():
            raise FileNotFoundError(
                f"The SO-101 model is missing at {path}. The benchtop-sim install is incomplete; "
                "reinstall it with `uv sync --all-packages --all-groups`."
            )
        return Path(path)
