# SPDX-FileCopyrightText: 2026 Benchtop Lab contributors
# SPDX-License-Identifier: Apache-2.0
"""Scene builder: the compiled model has the right structure and keeps the upstream arm's physics."""

from __future__ import annotations

import itertools
import math
import warnings
from typing import TYPE_CHECKING, Any

import mujoco
import numpy as np
import pytest

from benchtop_sim.builder import FLOOR_GEOM, MOUNT_SITE, TABLE_GEOM, build_model, build_spec
from benchtop_sim.scene import CameraSpec, LightSpec, ObjectSpec, RobotSpec, SceneSpec, TableSpec
from benchtop_sim.so101 import HOME, JOINTS, so101_model_path
from benchtop_sim.units import lerobot_to_ctrl

if TYPE_CHECKING:
    from pathlib import Path

CUBE = ObjectSpec("cube", "box", (0.015, 0.015, 0.015), pos=(0.25, 0.0, 0.015), rgba=(0.84, 0.37, 0.0, 1.0))
TARGET = ObjectSpec("target", "sphere", (0.02,), pos=(0.25, 0.1, 0.12), movable=False, collide=False)
WALL = ObjectSpec("wall", "box", (0.005, 0.08, 0.04), pos=(0.30, -0.15, 0.04), movable=False)
PUCK = ObjectSpec("puck", "cylinder", (0.02, 0.01), pos=(0.20, 0.15, 0.01), mass=0.05)


@pytest.fixture(scope="module")
def arm() -> Any:
    """The upstream arm compiled on its own, as the reference for parity checks."""
    return mujoco.MjModel.from_xml_path(str(so101_model_path()))


@pytest.fixture(scope="module")
def model() -> Any:
    return SceneSpec(objects=(CUBE, TARGET, WALL, PUCK)).build()


def set_pose(model: Any, data: Any, pose: tuple[float, ...]) -> None:
    """Put the arm at a pose given in LeRobot units and update derived quantities."""
    mujoco.mj_resetData(model, data)
    data.qpos[:6] = lerobot_to_ctrl(pose)
    data.ctrl[:] = data.qpos[:6]
    mujoco.mj_forward(model, data)


def contact_pairs(model: Any, data: Any) -> set[frozenset[str]]:
    """Names of the bodies in contact (touching or penetrating)."""
    pairs = set()
    for contact in data.contact[: data.ncon]:
        if contact.dist <= 0:
            bodies = (model.geom_bodyid[contact.geom1], model.geom_bodyid[contact.geom2])
            pairs.add(frozenset(model.body(body).name for body in bodies))
    return pairs


# --- structure ---------------------------------------------------------------------------------------------


def test_default_scene_compiles_without_warnings() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        model = SceneSpec().build()
    assert (model.nq, model.nu, model.ncam, model.nlight) == (6, 6, 2, 2)


def test_joint_and_actuator_names_match_lerobot_order(model: Any) -> None:
    assert [model.joint(i).name for i in range(6)] == list(JOINTS)
    assert [model.actuator(i).name for i in range(model.nu)] == list(JOINTS)
    assert model.actuator_trnid[:, 0].tolist() == list(range(6))


def test_arm_joints_come_first_in_qpos_whatever_the_objects(model: Any) -> None:
    assert [int(model.joint(name).qposadr[0]) for name in JOINTS] == list(range(6))
    assert [int(model.joint(name).dofadr[0]) for name in JOINTS] == list(range(6))
    # Two movable objects (cube, puck) add 7 qpos each, after the arm and in SceneSpec order.
    assert model.nq == 6 + 7 + 7
    assert int(model.joint("cube").qposadr[0]) == 6
    assert int(model.joint("puck").qposadr[0]) == 13


def test_cameras_are_front_then_wrist(model: Any) -> None:
    assert [model.camera(i).name for i in range(model.ncam)] == ["front", "wrist"]
    assert mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_CAMERA, "wrist_cam") == -1  # renamed, not duplicated
    assert model.body(model.cam_bodyid[model.camera("wrist").id]).name == "camera_mount"
    assert model.cam_bodyid[model.camera("front").id] == 0  # fixed to the world
    assert model.cam_fovy[model.camera("wrist").id] == pytest.approx(61.0)  # upstream value


def test_wrist_camera_moves_with_the_gripper_and_front_camera_does_not(model: Any) -> None:
    data = mujoco.MjData(model)
    set_pose(model, data, (0.0, 0.0, 0.0, 0.0, 0.0, 50.0))
    wrist_before, front_before = data.cam("wrist").xpos.copy(), data.cam("front").xpos.copy()
    set_pose(model, data, (40.0, -30.0, 30.0, 0.0, 0.0, 50.0))
    assert np.linalg.norm(data.cam("wrist").xpos - wrist_before) > 0.05
    np.testing.assert_array_equal(data.cam("front").xpos, front_before)


def test_front_camera_pose_matches_the_spec() -> None:
    spec = CameraSpec(pos=(0.6, 0.3, 0.5), lookat=(0.2, 0.0, 0.05), fovy_deg=50.0)
    model = SceneSpec(cameras={"front": spec}).build()
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    camera = data.cam("front")
    np.testing.assert_allclose(camera.xpos, spec.pos)
    forward = -camera.xmat.reshape(3, 3)[:, 2]  # MuJoCo cameras look along -z
    expected = np.array(spec.lookat) - np.array(spec.pos)
    np.testing.assert_allclose(forward, expected / np.linalg.norm(expected), atol=1e-9)
    assert camera.xmat.reshape(3, 3)[2, 1] > 0  # image "up" has a positive world-z component
    assert model.cam_fovy[model.camera("front").id] == pytest.approx(50.0)


def test_extra_cameras_and_wrist_fovy_override() -> None:
    top = CameraSpec(pos=(0.2, 0.0, 0.9), lookat=(0.2, 0.0, 0.0), up=(1.0, 0.0, 0.0))
    scene = SceneSpec(cameras={**SceneSpec().cameras, "top": top}, robot=RobotSpec(wrist_fovy_deg=75.0))
    model = scene.build()
    assert tuple(model.camera(i).name for i in range(model.ncam)) == scene.camera_names
    assert model.cam_fovy[model.camera("wrist").id] == pytest.approx(75.0)


def test_lights_follow_the_spec() -> None:
    lights = (
        LightSpec("sun", direction=(0.0, 1.0, -1.0), diffuse=(0.5, 0.4, 0.3)),
        LightSpec("lamp", pos=(0.2, 0.0, 0.8), directional=False, cast_shadow=False),
    )
    model = SceneSpec(lights=lights).build()
    assert [model.light(i).name for i in range(model.nlight)] == ["sun", "lamp"]
    assert model.light_type.tolist() == [
        mujoco.mjtLightType.mjLIGHT_DIRECTIONAL,
        mujoco.mjtLightType.mjLIGHT_SPOT,
    ]
    assert model.light_castshadow.tolist() == [1, 0]
    np.testing.assert_allclose(model.light_diffuse[0], (0.5, 0.4, 0.3))
    np.testing.assert_allclose(model.light_dir[0], np.array([0.0, 1.0, -1.0]) / math.sqrt(2))
    np.testing.assert_allclose(model.light_pos[1], (0.2, 0.0, 0.8))


def test_offscreen_buffer_fits_the_largest_supported_image(model: Any) -> None:
    assert (model.vis.global_.offwidth, model.vis.global_.offheight) == (640, 480)


# --- table, floor, mount -----------------------------------------------------------------------------------


def test_table_top_is_the_plane_z_equals_zero_and_floor_is_below() -> None:
    table = TableSpec(center=(0.3, 0.1), half_size=(0.35, 0.5), thickness=0.04, height=0.7)
    model = SceneSpec(table=table).build()
    top = model.geom(TABLE_GEOM)
    assert top.pos[2] + top.size[2] == pytest.approx(0.0)
    np.testing.assert_allclose(top.pos[:2], (0.3, 0.1))
    np.testing.assert_allclose(top.size, (0.35, 0.5, 0.02))
    floor = model.geom(FLOOR_GEOM)
    assert floor.type == mujoco.mjtGeom.mjGEOM_PLANE
    assert floor.pos[2] == pytest.approx(-0.7)
    for index in range(4):
        leg = model.geom(f"table_leg_{index}")
        assert leg.pos[2] + leg.size[2] == pytest.approx(-0.04)  # touches the underside of the top
        assert leg.pos[2] - leg.size[2] == pytest.approx(-0.7)  # stands on the floor
        assert abs(leg.pos[0] - 0.3) + leg.size[0] <= 0.35  # inside the footprint
        assert abs(leg.pos[1] - 0.1) + leg.size[1] <= 0.5


def test_table_friction_and_colour_follow_the_spec() -> None:
    table = TableSpec(friction=(0.6, 0.01, 0.001), rgba=(0.2, 0.3, 0.4, 1.0))
    model = SceneSpec(table=table).build()
    np.testing.assert_allclose(model.geom(TABLE_GEOM).friction, (0.6, 0.01, 0.001))
    np.testing.assert_allclose(model.mat_rgba[model.geom(TABLE_GEOM).matid[0]], (0.2, 0.3, 0.4, 1.0))


def test_arm_is_mounted_at_the_origin_facing_plus_x(model: Any) -> None:
    data = mujoco.MjData(model)
    set_pose(model, data, (0.0, 0.0, 0.0, 0.0, 0.0, 50.0))
    np.testing.assert_array_equal(model.body("base").pos, (0.0, 0.0, 0.0))
    np.testing.assert_array_equal(data.site(MOUNT_SITE).xpos, (0.0, 0.0, 0.0))
    tip = data.site("gripperframe").xpos
    assert tip[0] > 0.3  # stretched out towards +x
    assert abs(tip[1]) < 0.01
    assert tip[2] > 0.05  # above the table


def test_mount_pose_moves_and_turns_the_whole_arm(model: Any) -> None:
    moved = SceneSpec(robot=RobotSpec(mount_pos=(0.1, -0.2, 0.0), mount_yaw_deg=90.0)).build()
    pose = (20.0, -30.0, 40.0, 10.0, 0.0, 50.0)
    reference, data = mujoco.MjData(model), mujoco.MjData(moved)
    set_pose(model, reference, pose)
    set_pose(moved, data, pose)
    quarter_turn = np.array([[0.0, -1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]])
    for site in ("gripperframe", "baseframe"):
        expected = quarter_turn @ reference.site(site).xpos + np.array([0.1, -0.2, 0.0])
        np.testing.assert_allclose(data.site(site).xpos, expected, atol=1e-9)
    np.testing.assert_allclose(data.site(MOUNT_SITE).xpos, (0.1, -0.2, 0.0))
    np.testing.assert_allclose(data.site(MOUNT_SITE).xmat.reshape(3, 3), quarter_turn, atol=1e-12)


def test_arm_does_not_touch_the_table_at_home_or_stretched_out(model: Any) -> None:
    data = mujoco.MjData(model)
    for pose in (HOME, (0.0, 0.0, 0.0, 0.0, 0.0, 50.0)):
        set_pose(model, data, pose)
        arm_contacts = {pair for pair in contact_pairs(model, data) if pair != frozenset({"world", "cube"})}
        assert arm_contacts <= {frozenset({"world", "puck"})}, arm_contacts


def test_arm_collides_with_the_table_when_driven_into_it(model: Any) -> None:
    # Adversarial: if the table had no collision geometry, tasks could be "solved" through the table.
    data = mujoco.MjData(model)
    set_pose(model, data, (0.0, 60.0, 30.0, 60.0, 0.0, 50.0))  # gripper pushed below z = 0
    table = model.geom(TABLE_GEOM).id
    gripper_bodies = {model.body(name).id for name in ("gripper", "moving_jaw_so101_v1", "camera_mount")}
    hits = [
        contact
        for contact in data.contact[: data.ncon]
        if table in (contact.geom1, contact.geom2)
        and {int(model.geom_bodyid[contact.geom1]), int(model.geom_bodyid[contact.geom2])} & gripper_bodies
    ]
    assert hits
    assert min(contact.dist for contact in hits) < 0


# --- physics parity with upstream --------------------------------------------------------------------------


def test_physics_options_equal_the_standalone_arm(model: Any, arm: Any) -> None:
    fields = [name for name in dir(arm.opt) if not name.startswith("_")]
    assert {"timestep", "integrator", "cone", "impratio", "iterations", "ls_iterations"} <= set(fields)
    for name in fields:
        np.testing.assert_array_equal(getattr(model.opt, name), getattr(arm.opt, name), err_msg=name)


def test_joint_and_actuator_parameters_equal_the_standalone_arm(model: Any, arm: Any) -> None:
    for name in ("jnt_range", "jnt_axis", "jnt_pos", "jnt_limited"):
        np.testing.assert_array_equal(getattr(model, name)[:6], getattr(arm, name), err_msg=name)
    for name in ("dof_damping", "dof_armature", "dof_frictionloss"):
        np.testing.assert_array_equal(getattr(model, name)[:6], getattr(arm, name), err_msg=name)
    for name in ("actuator_ctrlrange", "actuator_forcerange", "actuator_gainprm", "actuator_biasprm"):
        np.testing.assert_array_equal(getattr(model, name), getattr(arm, name), err_msg=name)


def test_arm_bodies_and_collision_geometry_equal_the_standalone_arm(model: Any, arm: Any) -> None:
    for body in range(1, arm.nbody):
        name = arm.body(body).name
        ours = model.body(name).id
        np.testing.assert_array_equal(model.body_mass[ours], arm.body_mass[body], err_msg=name)
        np.testing.assert_array_equal(model.body_inertia[ours], arm.body_inertia[body], err_msg=name)
        if name != "base":  # the base is the body the mount moves
            np.testing.assert_array_equal(model.body_pos[ours], arm.body_pos[body], err_msg=name)
            np.testing.assert_array_equal(model.body_quat[ours], arm.body_quat[body], err_msg=name)
    named = [geom for geom in range(arm.ngeom) if arm.geom(geom).name]
    assert len(named) >= 20  # the tuned gripper pads and tips are all named upstream
    for geom in named:
        name = arm.geom(geom).name
        ours = model.geom(name).id
        for field in ("geom_friction", "geom_solref", "geom_solimp", "geom_condim", "geom_priority",
                      "geom_size", "geom_pos", "geom_quat", "geom_contype", "geom_conaffinity"):  # fmt: skip
            np.testing.assert_array_equal(
                getattr(model, field)[ours], getattr(arm, field)[geom], err_msg=name
            )


def test_forward_kinematics_equal_the_standalone_arm(model: Any, arm: Any) -> None:
    rng = np.random.default_rng(5)
    scene_data, arm_data = mujoco.MjData(model), mujoco.MjData(arm)
    for _ in range(5):
        q = rng.uniform(arm.actuator_ctrlrange[:, 0], arm.actuator_ctrlrange[:, 1])
        scene_data.qpos[:6] = q
        arm_data.qpos[:] = q
        mujoco.mj_kinematics(model, scene_data)
        mujoco.mj_kinematics(arm, arm_data)
        np.testing.assert_allclose(
            scene_data.site("gripperframe").xpos, arm_data.site("gripperframe").xpos, atol=1e-12
        )


# --- gripper geometry --------------------------------------------------------------------------------------


def jaw_gap(model: Any, data: Any, opening: float) -> float:
    set_pose(model, data, (0.0, 0.0, 0.0, 0.0, 0.0, opening))
    tips = data.geom("fixed_jaw_sph_tip1").xpos - data.geom("moving_jaw_sph_tip1").xpos
    return float(np.linalg.norm(tips))


def test_gripper_0_is_closed_and_100_is_open(model: Any) -> None:
    data = mujoco.MjData(model)
    closed, half, opened = (jaw_gap(model, data, opening) for opening in (0.0, 50.0, 100.0))
    assert closed < 0.006  # jaw tips within a few millimetres: nothing graspable fits between them
    assert opened > 0.10  # wide enough for a 3 cm cube with room to spare
    assert closed < half < opened


def test_gripper_gap_grows_monotonically_with_the_command(model: Any) -> None:
    data = mujoco.MjData(model)
    gaps = [jaw_gap(model, data, opening) for opening in range(0, 101, 10)]
    assert all(later > earlier for earlier, later in itertools.pairwise(gaps))


def test_closed_gripper_jaws_do_not_interpenetrate(model: Any) -> None:
    data = mujoco.MjData(model)
    set_pose(model, data, (0.0, 0.0, 0.0, 0.0, 0.0, 0.0))
    jaws = frozenset({"gripper", "moving_jaw_so101_v1"})
    depths = [
        contact.dist
        for contact in data.contact[: data.ncon]
        if frozenset(model.body(model.geom_bodyid[g]).name for g in (contact.geom1, contact.geom2)) == jaws
    ]
    assert all(depth > -0.002 for depth in depths)


def test_position_actuators_drive_the_arm_to_a_target_in_lerobot_units(model: Any) -> None:
    data = mujoco.MjData(model)
    set_pose(model, data, HOME)
    target = (25.0, -40.0, 50.0, 30.0, -20.0, 80.0)
    data.ctrl[:] = lerobot_to_ctrl(target)
    mujoco.mj_step(model, data, nstep=400)  # 2 s
    reached = np.rad2deg(data.qpos[:5])
    np.testing.assert_allclose(reached, target[:5], atol=2.0)  # gravity sag stays within 2 degrees
    assert data.qpos[5] == pytest.approx(lerobot_to_ctrl(target)[5], abs=0.03)


# --- objects -----------------------------------------------------------------------------------------------


def test_objects_have_the_requested_shape_pose_and_colour(model: Any) -> None:
    assert model.geom("cube").type == mujoco.mjtGeom.mjGEOM_BOX
    assert model.geom("target").type == mujoco.mjtGeom.mjGEOM_SPHERE
    assert model.geom("puck").type == mujoco.mjtGeom.mjGEOM_CYLINDER
    np.testing.assert_allclose(model.geom("cube").size, (0.015, 0.015, 0.015))
    np.testing.assert_allclose(model.geom("target").size[0], 0.02)
    np.testing.assert_allclose(model.geom("puck").size[:2], (0.02, 0.01))
    np.testing.assert_allclose(model.body("cube").pos, CUBE.pos)
    np.testing.assert_allclose(model.geom("cube").rgba, CUBE.rgba, atol=1e-6)
    assert model.body("cube").mass[0] == pytest.approx(0.02)
    assert model.body("puck").mass[0] == pytest.approx(0.05)


def test_movable_objects_get_a_free_joint_and_static_ones_none(model: Any) -> None:
    assert model.body("cube").jntnum[0] == 1
    assert model.joint("cube").type[0] == mujoco.mjtJoint.mjJNT_FREE
    assert model.body("wall").jntnum[0] == 0
    assert model.body("target").jntnum[0] == 0


def test_object_orientation_is_applied() -> None:
    half = math.sqrt(0.5)
    turned = ObjectSpec("bar", "box", (0.04, 0.01, 0.01), pos=(0.25, 0.0, 0.01), quat=(half, 0.0, 0.0, half))
    model = SceneSpec(objects=(turned,)).build()
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    long_axis = data.geom("bar").xmat.reshape(3, 3)[:, 0]
    np.testing.assert_allclose(long_axis, (0.0, 1.0, 0.0), atol=1e-9)


def test_cube_rests_on_the_table_and_stays_put(model: Any) -> None:
    data = mujoco.MjData(model)
    set_pose(model, data, HOME)
    mujoco.mj_step(model, data, nstep=300)
    cube = data.body("cube")
    assert cube.xpos[2] == pytest.approx(0.015, abs=0.001)  # resting on z = 0, not sinking or floating
    np.testing.assert_allclose(cube.xpos[:2], CUBE.pos[:2], atol=1e-3)
    assert np.linalg.norm(data.qvel[6:9]) < 1e-3
    assert frozenset({"world", "cube"}) in contact_pairs(model, data)


def test_marker_objects_touch_nothing_even_when_overlapped(model: Any) -> None:
    data = mujoco.MjData(model)
    set_pose(model, data, HOME)
    data.qpos[6:9] = TARGET.pos  # put the cube inside the target marker
    mujoco.mj_forward(model, data)
    assert not any("target" in pair for pair in contact_pairs(model, data))
    assert (model.geom("target").contype[0], model.geom("target").conaffinity[0]) == (0, 0)


def test_static_obstacle_blocks_a_movable_object(model: Any) -> None:
    data = mujoco.MjData(model)
    set_pose(model, data, HOME)
    data.qpos[6:9] = (WALL.pos[0] - 0.015, WALL.pos[1], 0.015)  # cube overlapping the wall
    mujoco.mj_forward(model, data)
    assert frozenset({"wall", "cube"}) in contact_pairs(model, data)


# --- errors ------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("name", ["gripper", "base", "table", "floor"])
def test_object_name_that_is_already_taken_is_explained(name: str) -> None:
    clash = ObjectSpec(name, "box", (0.01, 0.01, 0.01), pos=(0.25, 0.0, 0.01))
    with pytest.raises(ValueError, match=rf"could not build the scene.*'{name}'.*already used.*rename"):
        SceneSpec(objects=(clash,)).build()


def test_missing_robot_model_is_explained(tmp_path: Path) -> None:
    scene = SceneSpec(robot=RobotSpec(model_path=tmp_path / "nope.xml"))
    with pytest.raises(ValueError, match=r"Could not load the robot model .*nope\.xml.*uv sync"):
        build_model(scene)


def test_robot_model_without_wrist_camera_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "arm.xml"
    path.write_text('<mujoco><worldbody><body name="base"><geom size="0.01"/></body></worldbody></mujoco>')
    with pytest.raises(ValueError, match=r"has no camera named 'wrist_cam'.*'wrist' camera"):
        build_model(SceneSpec(robot=RobotSpec(model_path=path)))


def test_robot_model_must_have_one_root_body(tmp_path: Path) -> None:
    path = tmp_path / "two_roots.xml"
    path.write_text(
        '<mujoco><worldbody><body name="a"><geom size="0.01"/><camera name="wrist_cam"/></body>'
        '<body name="b"><geom size="0.01"/></body></worldbody></mujoco>'
    )
    with pytest.raises(ValueError, match="exactly one root body under the world, found 2"):
        build_model(SceneSpec(robot=RobotSpec(model_path=path)))


def test_build_spec_returns_an_editable_spec_and_builds_are_independent() -> None:
    scene = SceneSpec(objects=(CUBE,))
    spec = build_spec(scene)
    assert spec.modelname == "benchtop_so101_scene"
    spec.worldbody.add_geom(name="extra", size=(0.01, 0.0, 0.0), pos=(0.3, 0.2, 0.01))
    assert (
        spec.compile().ngeom == scene.build().ngeom + 1
    )  # editing one spec does not leak into the next build


def test_same_spec_builds_identical_models() -> None:
    scene = SceneSpec(objects=(CUBE, PUCK))
    first, second = scene.build(), scene.build()
    for name in (
        "qpos0",
        "body_pos",
        "body_mass",
        "geom_size",
        "geom_pos",
        "cam_pos",
        "cam_quat",
        "light_dir",
    ):
        np.testing.assert_array_equal(getattr(first, name), getattr(second, name), err_msg=name)
