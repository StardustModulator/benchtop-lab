# SPDX-FileCopyrightText: 2026 Benchtop Lab contributors
# SPDX-License-Identifier: Apache-2.0
"""Assemble a `SceneSpec` into a MuJoCo model with `mujoco.MjSpec`.

The vendored Menagerie SO-101 file is loaded unmodified and becomes the root of the scene: its base is moved
to the mount on the table, and the table, floor, lights, cameras and task objects are added around it. Working
on the arm's own spec keeps its physics options (integrator, timestep, friction cone, solver iterations),
defaults and joint, actuator and gripper-contact parameters exactly as upstream tuned them, and keeps the
joint names free of prefixes. Tests compare the built scene against the stand-alone arm to guard that.
"""

from __future__ import annotations

import math
from contextlib import contextmanager
from typing import TYPE_CHECKING, Final

import mujoco

from benchtop_sim.scene import (
    WRIST_CAMERA,
    CameraSpec,
    LightSpec,
    ObjectSpec,
    RobotSpec,
    SceneSpec,
    TableSpec,
)
from benchtop_sim.so101 import UPSTREAM_WRIST_CAMERA, so101_model_path

if TYPE_CHECKING:
    from collections.abc import Iterator

__all__ = ["FLOOR_GEOM", "MOUNT_SITE", "TABLE_GEOM", "build_model", "build_spec"]

MOUNT_SITE: Final[str] = "so101_mount"
"""Site marking the pose of the arm's base frame on the table top."""
TABLE_GEOM: Final[str] = "table"
"""Name of the table-top geom (success checks test contacts against it)."""
FLOOR_GEOM: Final[str] = "floor"
"""Name of the floor plane."""

_SHAPES: Final[dict[str, mujoco.mjtGeom]] = {
    "box": mujoco.mjtGeom.mjGEOM_BOX,
    "sphere": mujoco.mjtGeom.mjGEOM_SPHERE,
    "cylinder": mujoco.mjtGeom.mjGEOM_CYLINDER,
}

_LEG_HALF_WIDTH: Final[float] = 0.02
_LEG_INSET: Final[float] = 0.04
_LEG_RGBA: Final[tuple[float, float, float, float]] = (0.30, 0.31, 0.33, 1.0)
_FLOOR_RGB: Final[tuple[tuple[float, float, float], tuple[float, float, float]]] = (
    (0.47, 0.49, 0.52),
    (0.45, 0.47, 0.50),
)
_SKY_RGB: Final[tuple[tuple[float, float, float], tuple[float, float, float]]] = (
    (0.90, 0.92, 0.94),
    (0.66, 0.70, 0.75),
)
# Largest image the offscreen renderer may produce (the official Space's 480x640).
_OFFSCREEN_SIZE: Final[tuple[int, int]] = (640, 480)


def build_spec(scene: SceneSpec) -> mujoco.MjSpec:
    """Assemble the scene as an editable `mujoco.MjSpec` (call `.compile()` to get the model).

    Args:
        scene: The scene description.

    Raises:
        ValueError: If the robot model cannot be read or lacks its wrist camera, or a name in the scene is
            already used by the robot model.
    """
    spec = _load_arm(scene)
    spec.modelname = "benchtop_so101_scene"
    _mount_arm(spec, scene.robot)
    with _explain_mujoco_errors():
        _add_environment(spec, scene.table)
        for light in scene.lights:
            _add_light(spec, light)
        for name, camera in scene.cameras.items():
            _add_camera(spec, name, camera)
        # Objects come after the arm, so the arm's six joints are always qpos[0:6].
        for obj in scene.objects:
            _add_object(spec, obj)
    return spec


def build_model(scene: SceneSpec) -> mujoco.MjModel:
    """Compile a scene into a `mujoco.MjModel`.

    Args:
        scene: The scene description.

    Raises:
        ValueError: If MuJoCo rejects the scene, most often because an object, camera or light reuses a
            name that the robot model already defines.
    """
    spec = build_spec(scene)
    with _explain_mujoco_errors():
        return spec.compile()


@contextmanager
def _explain_mujoco_errors() -> Iterator[None]:
    """Re-raise MuJoCo's terse errors with the likely cause and the fix."""
    try:
        yield
    except ValueError as error:
        raise ValueError(
            f"MuJoCo could not build the scene: {error}. The usual cause is an object, camera or light "
            "whose name is already used by the robot model or the scene (for example 'gripper', 'base', "
            "'table' or 'floor'); rename it."
        ) from error


def _load_arm(scene: SceneSpec) -> mujoco.MjSpec:
    path = scene.robot.model_path or so101_model_path()
    try:
        arm = mujoco.MjSpec.from_file(str(path))
    except ValueError as error:
        raise ValueError(
            f"Could not load the robot model {path}: {error}. Check that the file and the meshes next to "
            "it exist; for the vendored model, reinstall with `uv sync --all-packages --all-groups`."
        ) from error
    wrist = arm.camera(UPSTREAM_WRIST_CAMERA)
    if wrist is None:
        raise ValueError(
            f"The robot model {path} has no camera named {UPSTREAM_WRIST_CAMERA!r}; Benchtop Lab needs it "
            f"as the {WRIST_CAMERA!r} camera. Use the vendored model or add that camera to the gripper."
        )
    wrist.name = WRIST_CAMERA
    if scene.robot.wrist_fovy_deg is not None:
        wrist.fovy = scene.robot.wrist_fovy_deg
    return arm


def _mount_arm(spec: mujoco.MjSpec, robot: RobotSpec) -> None:
    """Move the arm's root body to the mount pose and mark that pose with a site."""
    yaw = math.radians(robot.mount_yaw_deg)
    quat = (math.cos(yaw / 2), 0.0, 0.0, math.sin(yaw / 2))
    roots = [body for body in spec.worldbody.bodies if body.parent == spec.worldbody]
    if len(roots) != 1:
        raise ValueError(
            f"The robot model must have exactly one root body under the world, found {len(roots)}. "
            "Use the vendored SO-101 model (leave `RobotSpec.model_path` unset)."
        )
    # Upstream's root body sits at the world origin with no rotation, so the mount pose replaces it.
    roots[0].pos = robot.mount_pos
    roots[0].quat = quat
    spec.worldbody.add_site(name=MOUNT_SITE, pos=robot.mount_pos, quat=quat, group=5)


def _add_environment(spec: mujoco.MjSpec, table: TableSpec) -> None:
    """Add the sky, floor and table. The table top's upper face is the plane z = 0."""
    spec.visual.global_.offwidth, spec.visual.global_.offheight = _OFFSCREEN_SIZE
    spec.visual.headlight.ambient = (0.26, 0.26, 0.26)
    spec.visual.headlight.diffuse = (0.10, 0.10, 0.10)
    spec.visual.headlight.specular = (0.0, 0.0, 0.0)
    spec.visual.quality.shadowsize = 2048

    spec.add_texture(
        name="sky",
        type=mujoco.mjtTexture.mjTEXTURE_SKYBOX,
        builtin=mujoco.mjtBuiltin.mjBUILTIN_GRADIENT,
        rgb1=_SKY_RGB[0],
        rgb2=_SKY_RGB[1],
        width=128,
        height=768,
    )
    spec.add_texture(
        name="floor",
        type=mujoco.mjtTexture.mjTEXTURE_2D,
        builtin=mujoco.mjtBuiltin.mjBUILTIN_CHECKER,
        rgb1=_FLOOR_RGB[0],
        rgb2=_FLOOR_RGB[1],
        width=256,
        height=256,
    )
    floor_material = spec.add_material(name="floor", texrepeat=(4, 4), texuniform=True, reflectance=0.0)
    floor_material.textures[mujoco.mjtTextureRole.mjTEXROLE_RGB] = "floor"
    spec.add_material(name="table", rgba=table.rgba, specular=0.1, shininess=0.1, reflectance=0.0)
    spec.add_material(name="table_leg", rgba=_LEG_RGBA, specular=0.2, shininess=0.3)

    world = spec.worldbody
    world.add_geom(
        name=FLOOR_GEOM,
        type=mujoco.mjtGeom.mjGEOM_PLANE,
        pos=(0.0, 0.0, -table.height),
        size=(0.0, 0.0, 0.05),
        material="floor",
    )
    cx, cy = table.center
    hx, hy = table.half_size
    world.add_geom(
        name=TABLE_GEOM,
        type=mujoco.mjtGeom.mjGEOM_BOX,
        pos=(cx, cy, -table.thickness / 2),
        size=(hx, hy, table.thickness / 2),
        friction=table.friction,
        material="table",
    )
    leg_half_height = (table.height - table.thickness) / 2
    leg_dx = max(hx - _LEG_INSET, 0.0)
    leg_dy = max(hy - _LEG_INSET, 0.0)
    for index, (sx, sy) in enumerate(((1, 1), (1, -1), (-1, 1), (-1, -1))):
        world.add_geom(
            name=f"table_leg_{index}",
            type=mujoco.mjtGeom.mjGEOM_BOX,
            pos=(cx + sx * leg_dx, cy + sy * leg_dy, -table.thickness - leg_half_height),
            size=(min(_LEG_HALF_WIDTH, hx), min(_LEG_HALF_WIDTH, hy), leg_half_height),
            material="table_leg",
        )


def _add_light(spec: mujoco.MjSpec, light: LightSpec) -> None:
    spec.worldbody.add_light(
        name=light.name,
        pos=light.pos,
        dir=light.direction,
        diffuse=light.diffuse,
        specular=light.specular,
        type=mujoco.mjtLightType.mjLIGHT_DIRECTIONAL
        if light.directional
        else mujoco.mjtLightType.mjLIGHT_SPOT,
        castshadow=light.cast_shadow,
    )


def _add_camera(spec: mujoco.MjSpec, name: str, camera: CameraSpec) -> None:
    right, up = camera.xyaxes()
    added = spec.worldbody.add_camera(name=name, pos=camera.pos, fovy=camera.fovy_deg)
    added.alt.type = mujoco.mjtOrientation.mjORIENTATION_XYAXES
    added.alt.xyaxes = (*right, *up)


def _add_object(spec: mujoco.MjSpec, obj: ObjectSpec) -> None:
    body = spec.worldbody.add_body(name=obj.name, pos=obj.pos, quat=obj.quat)
    if obj.movable:
        body.add_freejoint(name=obj.name)
    size = [0.0, 0.0, 0.0]
    size[: len(obj.size)] = obj.size
    geom = body.add_geom(
        name=obj.name,
        type=_SHAPES[obj.shape],
        size=size,
        rgba=obj.rgba,
        mass=obj.mass,
        friction=obj.friction,
    )
    if not obj.collide:
        geom.contype = 0
        geom.conaffinity = 0
