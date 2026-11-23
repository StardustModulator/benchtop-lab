# SPDX-FileCopyrightText: 2026 Benchtop Lab contributors
# SPDX-License-Identifier: Apache-2.0
"""Offscreen rendering of the built scene (needs MUJOCO_GL=egl or osmesa)."""

from __future__ import annotations

from typing import Any

import mujoco
import numpy as np
import pytest

from benchtop_sim.scene import ObjectSpec, SceneSpec
from benchtop_sim.so101 import HOME
from benchtop_sim.units import lerobot_to_ctrl

pytestmark = pytest.mark.render

ORANGE = (0.84, 0.37, 0.0, 1.0)
CUBE = ObjectSpec("cube", "box", (0.015, 0.015, 0.015), pos=(0.25, 0.0, 0.015), rgba=ORANGE)


@pytest.fixture(scope="module")
def scene() -> tuple[Any, Any]:
    model = SceneSpec(objects=(CUBE,)).build()
    data = mujoco.MjData(model)
    data.qpos[:6] = lerobot_to_ctrl(HOME)
    mujoco.mj_forward(model, data)
    return model, data


def render(scene: tuple[Any, Any], camera: str, height: int = 128, width: int = 128) -> Any:
    model, data = scene
    with mujoco.Renderer(model, height, width) as renderer:
        renderer.update_scene(data, camera=camera)
        return renderer.render().copy()


def arm_yellow(image: Any) -> Any:
    """Mask of pixels with the upstream arm's yellow (strong red and green, little blue)."""
    red, green, blue = (image[..., channel].astype(int) for channel in range(3))
    return (red > 120) & (green > 90) & (blue < 90) & (red - blue > 80) & (green - blue > 50)


def cube_orange(image: Any) -> Any:
    red, green, blue = (image[..., channel].astype(int) for channel in range(3))
    return (red > 110) & (red - green > 50) & (green > blue + 15) & (blue < 70)


@pytest.mark.parametrize("camera", ["front", "wrist"])
def test_cameras_render_a_non_empty_128_image(scene: tuple[Any, Any], camera: str) -> None:
    image = render(scene, camera)
    assert image.shape == (128, 128, 3)
    assert image.dtype == np.uint8
    assert image.std() > 10  # not a flat colour
    assert len(np.unique(image.reshape(-1, 3), axis=0)) > 100  # real shading, not a few flat regions
    assert 30 < image.mean() < 225  # neither black nor blown out


def test_front_camera_shows_the_arm_and_the_cube(scene: tuple[Any, Any]) -> None:
    image = render(scene, "front")
    assert arm_yellow(image).mean() > 0.02  # the arm fills a visible part of the frame
    assert cube_orange(image).sum() >= 8  # the 3 cm cube is a few pixels wide at 128x128


def test_front_camera_keeps_the_arm_and_workspace_in_frame(scene: tuple[Any, Any]) -> None:
    rows, cols = np.nonzero(arm_yellow(render(scene, "front")))
    assert rows.min() > 2  # the arm is not cut off at the top
    assert cols.min() > 2
    assert cols.max() < 125
    cube_rows, _ = np.nonzero(cube_orange(render(scene, "front")))
    assert cube_rows.max() < 120  # room below the cube for the rest of the workspace


def test_front_and_wrist_views_differ(scene: tuple[Any, Any]) -> None:
    difference = np.abs(render(scene, "front").astype(int) - render(scene, "wrist").astype(int))
    assert difference.mean() > 5


def test_rendering_reflects_the_arm_pose(scene: tuple[Any, Any]) -> None:
    model, _ = scene
    data = mujoco.MjData(model)
    data.qpos[:6] = lerobot_to_ctrl((60.0, -20.0, 20.0, 30.0, 0.0, 100.0))
    mujoco.mj_forward(model, data)
    difference = np.abs(render(scene, "front").astype(int) - render((model, data), "front").astype(int))
    assert (difference.max(axis=-1) > 40).mean() > 0.02


def test_rendering_is_repeatable(scene: tuple[Any, Any]) -> None:
    np.testing.assert_array_equal(render(scene, "front"), render(scene, "front"))


def test_full_size_480x640_image_renders(scene: tuple[Any, Any]) -> None:
    image = render(scene, "front", height=480, width=640)
    assert image.shape == (480, 640, 3)
    assert arm_yellow(image).mean() > 0.02
