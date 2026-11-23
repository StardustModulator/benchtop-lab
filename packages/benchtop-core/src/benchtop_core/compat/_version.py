# SPDX-FileCopyrightText: 2026 Benchtop Lab contributors
# SPDX-License-Identifier: Apache-2.0
"""Which LeRobot is installed, and whether it is inside the range Benchtop Lab is tested against."""

from dataclasses import dataclass
from importlib import metadata
from typing import Final

from packaging.specifiers import SpecifierSet
from packaging.version import InvalidVersion, Version

from benchtop_core.errors import BenchtopError

__all__ = ["SUPPORTED_LEROBOT", "LeRobotVersion", "lerobot_version", "require_supported_lerobot"]

SUPPORTED_LEROBOT: Final = SpecifierSet(">=0.7,<0.8")
"""The pinned range (PLAN §2). LeRobot ships breaking changes in every minor release."""

_INSTALL_FIX: Final = 'uv sync --all-packages --all-groups   (or: pip install "lerobot[dataset]==0.7.*")'


@dataclass(frozen=True, slots=True)
class LeRobotVersion:
    """The installed LeRobot and the supported range.

    Attributes:
        installed: The installed version string, or `None` if LeRobot is not installed.
        required: The supported range as a version specifier, e.g. `<0.8,>=0.7`.
        supported: Whether the installed version is inside the range.
    """

    installed: str | None
    required: str
    supported: bool


def lerobot_version() -> LeRobotVersion:
    """Report the installed LeRobot version and whether it is in the supported range.

    Reads the package metadata, so it does not import `lerobot` (or `torch`) and is safe to call at start-up.

    Returns:
        The installed version (or `None`), the supported range and whether they match.
    """
    required = str(SUPPORTED_LEROBOT)
    try:
        installed = metadata.version("lerobot")
    except metadata.PackageNotFoundError:
        return LeRobotVersion(installed=None, required=required, supported=False)
    try:
        supported = SUPPORTED_LEROBOT.contains(Version(installed), prereleases=True)
    except InvalidVersion:
        supported = False
    return LeRobotVersion(installed=installed, required=required, supported=supported)


def require_supported_lerobot() -> LeRobotVersion:
    """Return the installed LeRobot version, or raise if it is missing or outside the supported range.

    Returns:
        The installed, supported version.

    Raises:
        BenchtopError: If LeRobot is not installed or its version is outside `SUPPORTED_LEROBOT`.
    """
    found = lerobot_version()
    if found.installed is None:
        raise BenchtopError(
            "LeRobot is not installed.",
            cause="the environment was created without Benchtop Lab's dependencies.",
            fix=_INSTALL_FIX,
        )
    if not found.supported:
        raise BenchtopError(
            f"LeRobot {found.installed} is installed, but Benchtop Lab supports lerobot{found.required}.",
            cause="LeRobot was upgraded or downgraded separately from Benchtop Lab.",
            fix=_INSTALL_FIX,
        )
    return found
