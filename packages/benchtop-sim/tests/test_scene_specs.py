# SPDX-FileCopyrightText: 2026 Benchtop Lab contributors
# SPDX-License-Identifier: Apache-2.0
"""Scene dataclasses: defaults, immutability and validation messages."""

from __future__ import annotations

import math
from dataclasses import FrozenInstanceError

import numpy as np
import pytest

from benchtop_sim.scene import (
    FRONT_CAMERA,
    WRIST_CAMERA,
    CameraSpec,
    LightSpec,
    ObjectSpec,
    RobotSpec,
    SceneSpec,
    TableSpec,
)


def cube(name: str = "cube") -> ObjectSpec:
    return ObjectSpec(name, "box", (0.015, 0.015, 0.015), pos=(0.25, 0.0, 0.015))


def test_default_scene_has_front_and_wrist_cameras_and_lights() -> None:
    scene = SceneSpec()
    assert scene.camera_names == (FRONT_CAMERA, WRIST_CAMERA) == ("front", "wrist")
    assert scene.objects == ()
    assert [light.name for light in scene.lights] == ["key", "fill"]
    assert scene.robot == RobotSpec()
    assert scene.table == TableSpec()


def test_specs_are_immutable_even_when_built_from_lists_and_dicts() -> None:
    cameras = {"front": CameraSpec(pos=(0.7, 0.0, 0.4), lookat=(0.2, 0.0, 0.0))}
    scene = SceneSpec(objects=[cube()], cameras=cameras, lights=[LightSpec("sun")])  # type: ignore[arg-type]
    assert isinstance(scene.objects, tuple)
    assert isinstance(scene.lights, tuple)
    cameras["extra"] = cameras["front"]  # the caller's dict is not the scene's
    assert list(scene.cameras) == ["front"]
    with pytest.raises(TypeError):
        scene.cameras["other"] = cameras["front"]  # type: ignore[index]
    with pytest.raises(FrozenInstanceError):
        scene.objects = ()  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        cube().mass = 1.0  # type: ignore[misc]


def test_equal_specs_compare_equal() -> None:
    assert SceneSpec(objects=(cube(),)) == SceneSpec(objects=(cube(),))
    assert SceneSpec(objects=(cube(),)) != SceneSpec(objects=(cube("other"),))


def test_extra_cameras_keep_insertion_order_before_wrist() -> None:
    front = CameraSpec(pos=(0.7, 0.0, 0.4), lookat=(0.2, 0.0, 0.0))
    top = CameraSpec(pos=(0.2, 0.0, 0.9), lookat=(0.2, 0.0, 0.0), up=(1.0, 0.0, 0.0))
    assert SceneSpec(cameras={"front": front, "top": top}).camera_names == ("front", "top", "wrist")


def test_scene_requires_front_camera() -> None:
    side = CameraSpec(pos=(0.2, -0.8, 0.3), lookat=(0.2, 0.0, 0.0))
    with pytest.raises(ValueError, match=r"needs a camera named 'front'.*observation\.images\.front"):
        SceneSpec(cameras={"side": side})


def test_scene_rejects_a_world_camera_named_wrist() -> None:
    camera = CameraSpec(pos=(0.7, 0.0, 0.4), lookat=(0.2, 0.0, 0.0))
    with pytest.raises(ValueError, match=r"'wrist' is the camera on the gripper.*wrist_fovy_deg"):
        SceneSpec(cameras={"front": camera, "wrist": camera})


def test_scene_rejects_duplicate_object_and_light_names() -> None:
    with pytest.raises(ValueError, match=r"duplicate object name\(s\) \['cube'\]"):
        SceneSpec(objects=(cube(), cube()))
    with pytest.raises(ValueError, match=r"duplicate light name\(s\) \['sun'\]"):
        SceneSpec(lights=(LightSpec("sun"), LightSpec("sun")))


@pytest.mark.parametrize("name", ["", "red cube", "cube-1", "cubé", "a/b"])
def test_names_must_be_plain_identifiers(name: str) -> None:
    with pytest.raises(ValueError, match="is not valid"):
        ObjectSpec(name, "sphere", (0.01,), pos=(0.2, 0.0, 0.01))
    with pytest.raises(ValueError, match="is not valid"):
        LightSpec(name)
    with pytest.raises(ValueError, match="is not valid"):
        SceneSpec(
            cameras={"front": CameraSpec((0.7, 0, 0.4), (0.2, 0, 0)), name: CameraSpec((1, 0, 1), (0, 0, 0))}
        )


# --- camera ------------------------------------------------------------------------------------------------


def test_camera_axes_are_orthonormal_and_look_at_the_target() -> None:
    camera = CameraSpec(pos=(0.7, -0.2, 0.4), lookat=(0.17, 0.0, 0.07))
    right, up = (np.array(axis) for axis in camera.xyaxes())
    forward = np.cross(up, right)  # the camera looks along -z = up x right
    expected = np.array(camera.lookat) - np.array(camera.pos)
    np.testing.assert_allclose(forward, expected / np.linalg.norm(expected), atol=1e-12)
    assert np.linalg.norm(right) == pytest.approx(1.0)
    assert np.linalg.norm(up) == pytest.approx(1.0)
    assert float(right @ up) == pytest.approx(0.0, abs=1e-12)
    assert right[2] == pytest.approx(0.0, abs=1e-12)  # image stays level
    assert up[2] > 0  # world +z is up in the image


def test_camera_rejects_degenerate_views() -> None:
    with pytest.raises(ValueError, match="same point"):
        CameraSpec(pos=(0.1, 0.2, 0.3), lookat=(0.1, 0.2, 0.3))
    with pytest.raises(ValueError, match=r"parallel to the viewing direction.*\(1, 0, 0\)"):
        CameraSpec(pos=(0.2, 0.0, 1.0), lookat=(0.2, 0.0, 0.0))
    CameraSpec(pos=(0.2, 0.0, 1.0), lookat=(0.2, 0.0, 0.0), up=(1.0, 0.0, 0.0))  # the suggested fix works


@pytest.mark.parametrize("fovy", [0.0, -10.0, 180.0, math.nan])
def test_camera_and_wrist_fovy_must_be_sensible(fovy: float) -> None:
    with pytest.raises(ValueError, match="`fovy_deg` must be between 1 and 179"):
        CameraSpec(pos=(0.7, 0.0, 0.4), lookat=(0.2, 0.0, 0.0), fovy_deg=fovy)
    with pytest.raises(ValueError, match="`wrist_fovy_deg` must be between 1 and 179"):
        RobotSpec(wrist_fovy_deg=fovy)


def test_camera_rejects_non_finite_and_wrong_length_vectors() -> None:
    with pytest.raises(ValueError, match="`pos` must be 3 finite numbers"):
        CameraSpec(pos=(math.inf, 0.0, 0.4), lookat=(0.2, 0.0, 0.0))
    with pytest.raises(ValueError, match="`lookat` must be 3 finite numbers"):
        CameraSpec(pos=(0.7, 0.0, 0.4), lookat=(0.2, 0.0))  # type: ignore[arg-type]


# --- robot, table, light -----------------------------------------------------------------------------------


def test_robot_spec_validation() -> None:
    with pytest.raises(ValueError, match="`mount_pos` must be 3 finite numbers"):
        RobotSpec(mount_pos=(0.0, math.nan, 0.0))
    with pytest.raises(ValueError, match="`mount_yaw_deg` must be a finite angle"):
        RobotSpec(mount_yaw_deg=math.inf)
    assert RobotSpec(wrist_fovy_deg=75.0).wrist_fovy_deg == 75.0


def test_table_spec_validation() -> None:
    with pytest.raises(ValueError, match="`half_size` must be positive"):
        TableSpec(half_size=(0.4, 0.0))
    with pytest.raises(ValueError, match="`friction` must not be negative"):
        TableSpec(friction=(-1.0, 0.005, 0.0001))
    with pytest.raises(ValueError, match="0 < thickness < height"):
        TableSpec(thickness=0.8, height=0.74)
    with pytest.raises(ValueError, match="0 < thickness < height"):
        TableSpec(thickness=0.0)
    with pytest.raises(ValueError, match="between 0 and 1"):
        TableSpec(rgba=(1.2, 0.5, 0.5, 1.0))
    with pytest.raises(ValueError, match="`center` must be 2 finite numbers"):
        TableSpec(center=(0.0, math.nan))


def test_light_spec_validation() -> None:
    with pytest.raises(ValueError, match="`direction` must not be the zero vector"):
        LightSpec("sun", direction=(0.0, 0.0, 0.0))
    with pytest.raises(ValueError, match="LightSpec 'sun': `diffuse` components must be between 0 and 1"):
        LightSpec("sun", diffuse=(2.0, 0.0, 0.0))
    with pytest.raises(ValueError, match="`specular` must be 3 finite numbers"):
        LightSpec("sun", specular=(0.1, 0.1, 0.1, 1.0))  # type: ignore[arg-type]


# --- objects -----------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("shape", "size", "hint"),
    [
        ("box", (0.01, 0.01), "half-length x, half-length y, half-length z"),
        ("sphere", (0.01, 0.01), "radius"),
        ("cylinder", (0.01,), "radius, half-height"),
        ("box", (0.01, 0.0, 0.01), "all positive"),
        ("sphere", (-0.01,), "all positive"),
        ("sphere", (math.nan,), "all positive"),
    ],
)
def test_object_size_must_fit_the_shape(shape: str, size: tuple[float, ...], hint: str) -> None:
    with pytest.raises(ValueError, match=rf"ObjectSpec 'thing': a {shape} needs `size` = .*{hint}"):
        ObjectSpec("thing", shape, size, pos=(0.2, 0.0, 0.02))  # type: ignore[arg-type]


def test_object_rejects_unknown_shape_and_lists_the_valid_ones() -> None:
    with pytest.raises(ValueError, match=r"unknown shape 'capsule'.*\['box', 'cylinder', 'sphere'\]"):
        ObjectSpec("thing", "capsule", (0.01, 0.02), pos=(0.2, 0.0, 0.02))  # type: ignore[arg-type]


def test_object_validation_of_pose_colour_mass_and_friction() -> None:
    with pytest.raises(ValueError, match="`quat` must be a unit quaternion"):
        ObjectSpec("thing", "sphere", (0.01,), pos=(0.2, 0.0, 0.02), quat=(1.0, 1.0, 0.0, 0.0))
    with pytest.raises(ValueError, match="`pos` must be 3 finite numbers"):
        ObjectSpec("thing", "sphere", (0.01,), pos=(0.2, math.inf, 0.02))
    with pytest.raises(ValueError, match="`rgba` components must be between 0 and 1"):
        ObjectSpec("thing", "sphere", (0.01,), pos=(0.2, 0.0, 0.02), rgba=(255.0, 0.0, 0.0, 1.0))
    with pytest.raises(ValueError, match="`friction` must not be negative"):
        ObjectSpec("thing", "sphere", (0.01,), pos=(0.2, 0.0, 0.02), friction=(1.0, -0.1, 0.0))
    for mass in (0.0, -1.0, math.nan, math.inf):
        with pytest.raises(ValueError, match="`mass` must be a positive number of kilograms"):
            ObjectSpec("thing", "sphere", (0.01,), pos=(0.2, 0.0, 0.02), mass=mass)
