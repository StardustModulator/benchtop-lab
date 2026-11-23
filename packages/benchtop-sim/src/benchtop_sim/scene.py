# SPDX-FileCopyrightText: 2026 Benchtop Lab contributors
# SPDX-License-Identifier: Apache-2.0
"""Declarative description of a tabletop scene: robot, table, objects, cameras and lights.

A `SceneSpec` is plain, immutable data. `SceneSpec.build()` hands it to `benchtop_sim.builder`, which
assembles the MuJoCo model with `mujoco.MjSpec` (never by templating XML).

**World frame.** The origin is on the table top, `z = 0` is the table surface and `+z` points up. With the
default mount the arm's base sits at the origin and the arm reaches towards `+x`; `+y` is the arm's left.
Lengths are metres, angles are degrees unless a field says otherwise.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TYPE_CHECKING, Final, Literal

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    import mujoco

__all__ = [
    "FRONT_CAMERA",
    "WRIST_CAMERA",
    "CameraSpec",
    "LightSpec",
    "ObjectSpec",
    "RobotSpec",
    "SceneSpec",
    "TableSpec",
]

type Vec3 = tuple[float, float, float]
type Quat = tuple[float, float, float, float]
type Rgba = tuple[float, float, float, float]
type Shape = Literal["box", "sphere", "cylinder"]

FRONT_CAMERA: Final[str] = "front"
"""Name of the scene camera every scene must define."""
WRIST_CAMERA: Final[str] = "wrist"
"""Name of the camera on the gripper; it comes with the robot model."""

_SIZE_FIELDS: Final[Mapping[str, tuple[str, ...]]] = MappingProxyType(
    {
        "box": ("half-length x", "half-length y", "half-length z"),
        "sphere": ("radius",),
        "cylinder": ("radius", "half-height"),
    }
)
_MIN_FOVY: Final[float] = 1.0
_MAX_FOVY: Final[float] = 179.0


def _finite(values: tuple[float, ...]) -> bool:
    return all(math.isfinite(value) for value in values)


def _check_vec(owner: str, name: str, values: tuple[float, ...], length: int) -> None:
    if len(values) != length or not _finite(values):
        raise ValueError(f"{owner}: `{name}` must be {length} finite numbers, got {values!r}.")


def _check_rgba(owner: str, name: str, values: tuple[float, ...], length: int = 4) -> None:
    _check_vec(owner, name, values, length)
    if any(not 0.0 <= value <= 1.0 for value in values):
        raise ValueError(f"{owner}: `{name}` components must be between 0 and 1, got {values!r}.")


def _check_name(owner: str, name: str) -> None:
    if not name or not name.replace("_", "").isalnum() or not name.isascii():
        raise ValueError(
            f"{owner}: name {name!r} is not valid. Use ASCII letters, digits and underscores ('red_cube')."
        )


@dataclass(frozen=True, slots=True)
class RobotSpec:
    """The SO-101 arm and where it is mounted on the table.

    Attributes:
        mount_pos: Position of the arm's base frame in the world frame (on the table top by default).
        mount_yaw_deg: Rotation of the base about `+z`; 0 means the arm reaches towards `+x`.
        model_path: MJCF of the arm; `None` uses the vendored Menagerie `robotstudio_so101/so101.xml`.
        wrist_fovy_deg: Vertical field of view of the wrist camera; `None` keeps the model's own (61°).
    """

    mount_pos: Vec3 = (0.0, 0.0, 0.0)
    mount_yaw_deg: float = 0.0
    model_path: Path | None = None
    wrist_fovy_deg: float | None = None

    def __post_init__(self) -> None:
        _check_vec("RobotSpec", "mount_pos", self.mount_pos, 3)
        if not math.isfinite(self.mount_yaw_deg):
            raise ValueError(
                f"RobotSpec: `mount_yaw_deg` must be a finite angle, got {self.mount_yaw_deg!r}."
            )
        if self.wrist_fovy_deg is not None and not _MIN_FOVY <= self.wrist_fovy_deg <= _MAX_FOVY:
            raise ValueError(
                f"RobotSpec: `wrist_fovy_deg` must be between {_MIN_FOVY:g} and {_MAX_FOVY:g} degrees, "
                f"got {self.wrist_fovy_deg!r}."
            )


@dataclass(frozen=True, slots=True)
class TableSpec:
    """The table the arm is mounted on. Its top surface is the plane `z = 0`.

    Attributes:
        center: `(x, y)` of the table top's centre in the world frame.
        half_size: Half-lengths of the top along `x` and `y`.
        thickness: Thickness of the top slab.
        height: Height of the top surface above the floor (the floor is at `z = -height`).
        rgba: Colour of the top.
        friction: MuJoCo friction coefficients (sliding, torsional, rolling).
    """

    center: tuple[float, float] = (0.22, 0.0)
    half_size: tuple[float, float] = (0.40, 0.45)
    thickness: float = 0.03
    height: float = 0.74
    rgba: Rgba = (0.74, 0.70, 0.64, 1.0)
    friction: Vec3 = (1.0, 0.005, 0.0001)

    def __post_init__(self) -> None:
        _check_vec("TableSpec", "center", self.center, 2)
        _check_vec("TableSpec", "half_size", self.half_size, 2)
        _check_rgba("TableSpec", "rgba", self.rgba)
        _check_vec("TableSpec", "friction", self.friction, 3)
        if min(self.half_size) <= 0 or min(self.friction) < 0:
            raise ValueError("TableSpec: `half_size` must be positive and `friction` must not be negative.")
        if not 0 < self.thickness < self.height or not math.isfinite(self.height):
            raise ValueError(
                f"TableSpec: need 0 < thickness < height, got thickness={self.thickness!r}, "
                f"height={self.height!r}."
            )


@dataclass(frozen=True, slots=True)
class CameraSpec:
    """A fixed scene camera that looks from `pos` at the point `lookat`.

    Attributes:
        pos: Camera position in the world frame.
        lookat: Point in the world frame that appears at the image centre.
        fovy_deg: Vertical field of view in degrees.
        up: Direction that should appear "up" in the image; must not be parallel to the viewing direction.
    """

    pos: Vec3
    lookat: Vec3
    fovy_deg: float = 45.0
    up: Vec3 = (0.0, 0.0, 1.0)

    def __post_init__(self) -> None:
        for name in ("pos", "lookat", "up"):
            _check_vec("CameraSpec", name, getattr(self, name), 3)
        if not _MIN_FOVY <= self.fovy_deg <= _MAX_FOVY:
            raise ValueError(
                f"CameraSpec: `fovy_deg` must be between {_MIN_FOVY:g} and {_MAX_FOVY:g} degrees, "
                f"got {self.fovy_deg!r}."
            )
        self.xyaxes()  # raises if the viewing direction is degenerate

    def xyaxes(self) -> tuple[Vec3, Vec3]:
        """Return the camera's image axes (right, up) as unit vectors in the world frame.

        MuJoCo cameras look along their `-z` axis with `+x` to the right and `+y` up in the image.

        Raises:
            ValueError: If `pos` equals `lookat`, or `up` is parallel to the viewing direction.
        """
        back = _normalised(_sub(self.pos, self.lookat))
        if back is None:
            raise ValueError(f"CameraSpec: `pos` and `lookat` are the same point {self.pos!r}.")
        right = _normalised(_cross(self.up, back))
        if right is None:
            raise ValueError(
                f"CameraSpec: `up` {self.up!r} is parallel to the viewing direction; choose another `up`, "
                "e.g. (1, 0, 0) for a camera looking straight down."
            )
        return right, _cross(back, right)


@dataclass(frozen=True, slots=True)
class LightSpec:
    """One light.

    Attributes:
        name: Unique light name.
        pos: Position in the world frame (ignored by MuJoCo for directional lights, except for shadows).
        direction: Direction the light shines in; need not be normalised.
        diffuse: Diffuse RGB intensity.
        specular: Specular RGB intensity.
        directional: `True` for a sun-like light, `False` for a spotlight at `pos`.
        cast_shadow: Whether the light casts shadows.
    """

    name: str
    pos: Vec3 = (0.0, 0.0, 1.5)
    direction: Vec3 = (0.0, 0.0, -1.0)
    diffuse: Vec3 = (0.6, 0.6, 0.6)
    specular: Vec3 = (0.1, 0.1, 0.1)
    directional: bool = True
    cast_shadow: bool = True

    def __post_init__(self) -> None:
        owner = f"LightSpec {self.name!r}"
        _check_name("LightSpec", self.name)
        _check_vec(owner, "pos", self.pos, 3)
        _check_vec(owner, "direction", self.direction, 3)
        _check_rgba(owner, "diffuse", self.diffuse, 3)
        _check_rgba(owner, "specular", self.specular, 3)
        if _normalised(self.direction) is None:
            raise ValueError(f"{owner}: `direction` must not be the zero vector.")


@dataclass(frozen=True, slots=True)
class ObjectSpec:
    """A primitive task object: a cube to pick, a target marker, a wall.

    Attributes:
        name: Unique name; the MuJoCo body and its geom both get this name.
        shape: `"box"`, `"sphere"` or `"cylinder"`.
        size: Box: three half-lengths. Sphere: radius. Cylinder: radius and half-height.
        pos: Position of the object's centre in the world frame.
        quat: Orientation as a unit quaternion `(w, x, y, z)`.
        rgba: Colour.
        mass: Mass in kilograms (only matters for movable objects).
        friction: MuJoCo friction coefficients (sliding, torsional, rolling).
        movable: `True` gives the object a free joint; `False` fixes it to the world.
        collide: `False` makes the object a visual marker that nothing touches (e.g. a reach target).
    """

    name: str
    shape: Shape
    size: tuple[float, ...]
    pos: Vec3
    quat: Quat = (1.0, 0.0, 0.0, 0.0)
    rgba: Rgba = (0.5, 0.5, 0.5, 1.0)
    mass: float = 0.02
    friction: Vec3 = (1.0, 0.005, 0.0001)
    movable: bool = True
    collide: bool = True

    def __post_init__(self) -> None:
        owner = f"ObjectSpec {self.name!r}"
        _check_name("ObjectSpec", self.name)
        if self.shape not in _SIZE_FIELDS:
            raise ValueError(f"{owner}: unknown shape {self.shape!r}; use one of {sorted(_SIZE_FIELDS)}.")
        expected = _SIZE_FIELDS[self.shape]
        if len(self.size) != len(expected) or not _finite(self.size) or min(self.size) <= 0:
            raise ValueError(
                f"{owner}: a {self.shape} needs `size` = ({', '.join(expected)}), all positive, "
                f"got {self.size!r}."
            )
        _check_vec(owner, "pos", self.pos, 3)
        _check_vec(owner, "quat", self.quat, 4)
        if abs(math.sqrt(sum(q * q for q in self.quat)) - 1.0) > 1e-6:  # noqa: PLR2004
            raise ValueError(f"{owner}: `quat` must be a unit quaternion (w, x, y, z), got {self.quat!r}.")
        _check_rgba(owner, "rgba", self.rgba)
        _check_vec(owner, "friction", self.friction, 3)
        if min(self.friction) < 0:
            raise ValueError(f"{owner}: `friction` must not be negative, got {self.friction!r}.")
        if not (math.isfinite(self.mass) and self.mass > 0):
            raise ValueError(f"{owner}: `mass` must be a positive number of kilograms, got {self.mass!r}.")


def _default_cameras() -> Mapping[str, CameraSpec]:
    # Opposite the arm, raised and slightly off-axis so the gripper does not hide the workspace.
    return {FRONT_CAMERA: CameraSpec(pos=(0.70, -0.20, 0.40), lookat=(0.17, 0.0, 0.07), fovy_deg=40.0)}


def _default_lights() -> tuple[LightSpec, ...]:
    return (
        LightSpec("key", pos=(0.3, -0.6, 1.6), direction=(0.05, 0.35, -1.0), diffuse=(0.50, 0.50, 0.48)),
        LightSpec(
            "fill",
            pos=(0.4, 0.8, 1.2),
            direction=(-0.1, -0.5, -1.0),
            diffuse=(0.14, 0.15, 0.17),
            specular=(0.0, 0.0, 0.0),
            cast_shadow=False,
        ),
    )


@dataclass(frozen=True, slots=True)
class SceneSpec:
    """A complete tabletop scene. Build the MuJoCo model with `build()`.

    Attributes:
        robot: The arm and its mount.
        table: The table.
        objects: Task objects, in a fixed order (their order decides the layout of `qpos`).
        cameras: Fixed scene cameras by name. Must contain `front`; `wrist` is reserved for the camera
            on the gripper, which the robot model provides.
        lights: Scene lights.

    Examples:
        >>> cube = ObjectSpec("cube", "box", (0.015, 0.015, 0.015), pos=(0.25, 0.0, 0.015))
        >>> scene = SceneSpec(objects=(cube,))
        >>> scene.camera_names
        ('front', 'wrist')
    """

    robot: RobotSpec = field(default_factory=RobotSpec)
    table: TableSpec = field(default_factory=TableSpec)
    objects: tuple[ObjectSpec, ...] = ()
    cameras: Mapping[str, CameraSpec] = field(default_factory=_default_cameras)
    lights: tuple[LightSpec, ...] = field(default_factory=_default_lights)

    def __post_init__(self) -> None:
        # Normalise containers so a spec is immutable even when built from lists and dicts.
        object.__setattr__(self, "objects", tuple(self.objects))
        object.__setattr__(self, "lights", tuple(self.lights))
        object.__setattr__(self, "cameras", MappingProxyType(dict(self.cameras)))
        for name in self.cameras:
            _check_name("SceneSpec camera", name)
        if FRONT_CAMERA not in self.cameras:
            raise ValueError(
                f"SceneSpec: the scene needs a camera named {FRONT_CAMERA!r} (LeRobot policies expect "
                f"`observation.images.{FRONT_CAMERA}`); got {sorted(self.cameras)}."
            )
        if WRIST_CAMERA in self.cameras:
            raise ValueError(
                f"SceneSpec: {WRIST_CAMERA!r} is the camera on the gripper and comes with the robot model; "
                "remove it from `cameras` (set `RobotSpec.wrist_fovy_deg` to change its field of view)."
            )
        _check_unique("object", [obj.name for obj in self.objects])
        _check_unique("light", [light.name for light in self.lights])

    @property
    def camera_names(self) -> tuple[str, ...]:
        """All camera names in the built model: scene cameras in insertion order, then `wrist`."""
        return (*self.cameras, WRIST_CAMERA)

    def build(self) -> mujoco.MjModel:
        """Compile the scene into a `mujoco.MjModel`.

        Raises:
            ValueError: If a name collides with one in the robot model, or MuJoCo rejects the scene.
        """
        from benchtop_sim.builder import build_model  # noqa: PLC0415  (builder imports this module)

        return build_model(self)


def _check_unique(kind: str, names: list[str]) -> None:
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise ValueError(
            f"SceneSpec: duplicate {kind} name(s) {duplicates}; every {kind} needs its own name."
        )


def _sub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _cross(a: Vec3, b: Vec3) -> Vec3:
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _normalised(v: Vec3) -> Vec3 | None:
    norm = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
    if norm < 1e-9:  # noqa: PLR2004
        return None
    return (v[0] / norm, v[1] / norm, v[2] / norm)
