# SPDX-FileCopyrightText: 2026 Benchtop Lab contributors
# SPDX-License-Identifier: Apache-2.0
"""The vendored SO-101 model: it compiles, matches LeRobot's joint order, and is an unmodified copy."""

from __future__ import annotations

import hashlib
import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import mujoco
import numpy as np
import pytest

from benchtop_sim import so101
from benchtop_sim.so101 import JOINT_LIMITS, JOINT_NAMES, JOINTS, JointLimit, joint_limit, so101_model_path

# What LeRobot 0.7 uses for the SO-101 follower: motor order in `so_follower` and its `<motor>.pos` features.
# Written out here on purpose, so that a change to `benchtop_sim.so101` cannot silently change the contract.
LEROBOT_MOTORS = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]
PINNED_COMMIT = "370c43965323c0944b433b202aac5058b5f907a9"


@pytest.fixture(scope="module")
def arm() -> Any:
    return mujoco.MjModel.from_xml_path(str(so101_model_path()))


def vendored_dir() -> Path:
    return so101_model_path().parent


def test_model_compiles_with_six_actuated_hinge_joints(arm: Any) -> None:
    assert (arm.nq, arm.nv, arm.nu, arm.njnt) == (6, 6, 6, 6)
    assert all(arm.jnt_type == mujoco.mjtJoint.mjJNT_HINGE)


def test_joint_names_and_order_match_lerobot(arm: Any) -> None:
    assert list(JOINTS) == LEROBOT_MOTORS
    assert [arm.joint(i).name for i in range(arm.njnt)] == LEROBOT_MOTORS
    assert [arm.actuator(i).name for i in range(arm.nu)] == LEROBOT_MOTORS
    # Actuator i drives joint i, and joint i is qpos[i]: no index mapping is needed anywhere.
    assert arm.actuator_trnid[:, 0].tolist() == list(range(6))
    assert arm.jnt_qposadr.tolist() == list(range(6))


def test_feature_names_and_lerobot_sim_contract() -> None:
    expected_names = [f"{motor}.pos" for motor in LEROBOT_MOTORS]
    assert list(JOINT_NAMES) == expected_names
    assert {
        "fps": 30,
        "control_mode": "position",
        "semantics": "so101-joint-degrees-v1",
        "state_names": expected_names,
        "action_names": expected_names,
        "robot_type": "so_follower",
    } == so101.LEROBOT_SIM
    assert tuple(LEROBOT_MOTORS[:5]) == so101.ARM_JOINTS
    assert so101.GRIPPER_JOINT == "gripper"
    assert so101.NUM_JOINTS == 6


def test_joint_limits_table_matches_the_compiled_model(arm: Any) -> None:
    assert [limit.name for limit in JOINT_LIMITS] == LEROBOT_MOTORS
    table = np.array([(limit.ctrl_min, limit.ctrl_max) for limit in JOINT_LIMITS])
    np.testing.assert_array_equal(table, arm.actuator_ctrlrange)
    assert all(arm.actuator_ctrllimited)
    # Every target the actuators accept is a position the joint can reach (ranges agree to rounding).
    assert np.all(table[:, 0] >= arm.jnt_range[:, 0] - 1e-5)
    assert np.all(table[:, 1] <= arm.jnt_range[:, 1] + 1e-5)


def test_joint_limits_in_lerobot_units() -> None:
    pan = joint_limit("shoulder_pan")
    assert pan.unit == "deg"
    assert pan.lerobot_min == pytest.approx(-110.0, abs=1e-3)
    assert pan.lerobot_max == pytest.approx(110.0, abs=1e-3)
    gripper = joint_limit("gripper.pos")
    assert (gripper.unit, gripper.lerobot_min, gripper.lerobot_max) == ("percent", 0.0, 100.0)
    assert [limit.unit for limit in JOINT_LIMITS] == ["deg"] * 5 + ["percent"]
    for limit in JOINT_LIMITS[:5]:
        assert limit.lerobot_min == pytest.approx(math.degrees(limit.ctrl_min))
        assert limit.lerobot_min < 0 < limit.lerobot_max  # zero is inside the range ("mid-range zero")


def test_joint_limit_rejects_unknown_joint_and_lists_valid_ones() -> None:
    with pytest.raises(KeyError, match=r"Unknown SO-101 joint 'elbow'.*shoulder_pan, shoulder_lift"):
        joint_limit("elbow")


def test_joint_limit_is_immutable() -> None:
    limit = JointLimit("gripper", -0.1, 1.0, "percent")
    with pytest.raises(AttributeError):
        limit.ctrl_min = 0.0  # type: ignore[misc]


def test_home_pose_is_within_limits() -> None:
    assert len(so101.HOME) == 6
    for value, limit in zip(so101.HOME, JOINT_LIMITS, strict=True):
        assert limit.lerobot_min <= value <= limit.lerobot_max


def test_model_keeps_upstream_physics_options(arm: Any) -> None:
    assert arm.opt.integrator == mujoco.mjtIntegrator.mjINT_IMPLICITFAST
    assert arm.opt.cone == mujoco.mjtCone.mjCONE_ELLIPTIC
    assert arm.opt.timestep == pytest.approx(0.005)


def test_missing_model_error_says_how_to_reinstall(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(so101, "files", lambda _package: tmp_path)
    with pytest.raises(
        FileNotFoundError, match=r"install is incomplete.*uv sync --all-packages --all-groups"
    ):
        so101_model_path()


# --- vendoring record --------------------------------------------------------------------------------------


def test_vendored_directory_has_licence_and_upstream_record() -> None:
    directory = vendored_dir()
    licence = (directory / "LICENSE").read_text(encoding="utf-8")
    assert "Apache License" in licence
    assert "Version 2.0, January 2004" in licence
    upstream = (directory / "UPSTREAM.md").read_text(encoding="utf-8")
    assert PINNED_COMMIT in upstream
    assert "github.com/google-deepmind/mujoco_menagerie" in upstream
    assert "SO-ARM100" in upstream  # derivation chain back to TheRobotStudio
    assert re.search(r"Vendored on \| \d{4}-\d{2}-\d{2}", upstream)


def test_notice_lists_the_vendored_model_at_the_pinned_commit() -> None:
    notice = (Path(__file__).parents[3] / "NOTICE").read_text(encoding="utf-8")
    assert PINNED_COMMIT in notice
    assert "packages/benchtop-sim/src/benchtop_sim/assets/robotstudio_so101/" in notice


def test_vendored_files_are_unmodified() -> None:
    directory = vendored_dir()
    recorded: dict[str, str] = {}
    for line in (directory / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        digest, name = line.split(maxsplit=1)
        recorded[name] = digest
    on_disk = {
        path.relative_to(directory).as_posix()
        for path in directory.rglob("*")
        if path.is_file() and path.name not in {"UPSTREAM.md", "SHA256SUMS"}
    }
    assert on_disk == set(recorded), "files were added to or removed from the vendored directory"
    for name, digest in recorded.items():
        assert hashlib.sha256((directory / name).read_bytes()).hexdigest() == digest, f"{name} was modified"


def test_every_mesh_the_model_references_is_vendored() -> None:
    root = ET.parse(so101_model_path()).getroot()  # noqa: S314
    meshes = [mesh.attrib["file"] for mesh in root.iter("mesh") if "file" in mesh.attrib]
    assert len(meshes) == 18
    assets = vendored_dir() / "assets"
    assert all((assets / name).is_file() for name in meshes)
