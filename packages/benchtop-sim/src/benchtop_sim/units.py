# SPDX-FileCopyrightText: 2026 Benchtop Lab contributors
# SPDX-License-Identifier: Apache-2.0
"""The one conversion between LeRobot units and MuJoCo actuator targets for the SO-101.

LeRobot units (`so_follower` with `use_degrees=True`): degrees for the five arm joints, zero at mid-range;
gripper opening from 0 (closed) to 100 (open). MuJoCo units: radians for all six position actuators.

The mapping is the official `lerobot/so101-tabletop-mujoco` Space's: arm joints are converted with
degrees → radians, the gripper is mapped linearly onto its actuator range, and the result is clipped to the
actuator limits. Environments, experts and tests all go through these functions; nothing else converts units.

Both functions are pure, accept any array whose last axis has the six joints in `JOINTS` order, and return
a new `float64` array.
"""

from __future__ import annotations

from typing import Final

import numpy as np
import numpy.typing as npt

from benchtop_sim.so101 import JOINT_LIMITS, JOINTS, NUM_JOINTS

__all__ = ["CTRL_MAX", "CTRL_MIN", "LEROBOT_MAX", "LEROBOT_MIN", "ctrl_to_lerobot", "lerobot_to_ctrl"]

FloatArray = npt.NDArray[np.float64]

_GRIPPER: Final[int] = NUM_JOINTS - 1


def _frozen(values: list[float]) -> FloatArray:
    array = np.array(values, dtype=np.float64)
    array.setflags(write=False)
    return array


CTRL_MIN: Final[FloatArray] = _frozen([limit.ctrl_min for limit in JOINT_LIMITS])
"""Lower actuator targets in radians, in `JOINTS` order (read-only)."""
CTRL_MAX: Final[FloatArray] = _frozen([limit.ctrl_max for limit in JOINT_LIMITS])
"""Upper actuator targets in radians, in `JOINTS` order (read-only)."""
LEROBOT_MIN: Final[FloatArray] = _frozen([limit.lerobot_min for limit in JOINT_LIMITS])
"""Lower limits in LeRobot units (degrees; 0 for the gripper), in `JOINTS` order (read-only)."""
LEROBOT_MAX: Final[FloatArray] = _frozen([limit.lerobot_max for limit in JOINT_LIMITS])
"""Upper limits in LeRobot units (degrees; 100 for the gripper), in `JOINTS` order (read-only)."""

_GRIPPER_SPAN: Final[float] = float(CTRL_MAX[_GRIPPER] - CTRL_MIN[_GRIPPER])


def _as_joint_array(values: npt.ArrayLike, what: str) -> FloatArray:
    array = np.array(values, dtype=np.float64)  # always a copy
    if array.ndim == 0 or array.shape[-1] != NUM_JOINTS:
        raise ValueError(
            f"{what} must have {NUM_JOINTS} values on its last axis, one per joint "
            f"({', '.join(JOINTS)}); got shape {array.shape}."
        )
    if not np.all(np.isfinite(array)):
        raise ValueError(
            f"{what} contains NaN or infinity. A policy that outputs non-finite values has usually "
            "diverged; check its normalisation statistics and inputs."
        )
    return array


def lerobot_to_ctrl(values: npt.ArrayLike) -> FloatArray:
    """Convert LeRobot joint values to MuJoCo actuator targets, clipped to the actuator limits.

    Args:
        values: Array-like of shape `(..., 6)`: degrees for the arm joints, 0 to 100 for the gripper.

    Returns:
        Actuator targets in radians, same shape, `float64`. Values beyond a limit are clipped to it, as a
        real servo would refuse to go further.

    Raises:
        ValueError: If the last axis does not have six values, or any value is NaN or infinite.

    Examples:
        >>> lerobot_to_ctrl([0, 0, 0, 0, 0, 100]).round(5).tolist()
        [0.0, 0.0, 0.0, 0.0, 0.0, 1.74533]
    """
    ctrl = _as_joint_array(values, "Joint values in LeRobot units")
    gripper = ctrl[..., _GRIPPER].copy()
    np.deg2rad(ctrl, out=ctrl)
    ctrl[..., _GRIPPER] = CTRL_MIN[_GRIPPER] + gripper / 100.0 * _GRIPPER_SPAN
    return np.clip(ctrl, CTRL_MIN, CTRL_MAX, out=ctrl)


def ctrl_to_lerobot(ctrl: npt.ArrayLike) -> FloatArray:
    """Convert MuJoCo joint positions or actuator targets (radians) to LeRobot units.

    This is the exact inverse of `lerobot_to_ctrl` inside the limits. It does **not** clip: a measured joint
    position slightly beyond a limit (the joint range is a soft constraint) is reported as it is, for example
    a gripper reading of -0.3.

    Args:
        ctrl: Array-like of shape `(..., 6)` in radians.

    Returns:
        Degrees for the arm joints and the 0 to 100 opening for the gripper, same shape, `float64`.

    Raises:
        ValueError: If the last axis does not have six values, or any value is NaN or infinite.
    """
    values = _as_joint_array(ctrl, "Joint positions in radians")
    gripper = values[..., _GRIPPER].copy()
    np.rad2deg(values, out=values)
    values[..., _GRIPPER] = (gripper - CTRL_MIN[_GRIPPER]) / _GRIPPER_SPAN * 100.0
    return values
