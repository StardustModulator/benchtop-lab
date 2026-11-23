# SPDX-FileCopyrightText: 2026 Benchtop Lab contributors
# SPDX-License-Identifier: Apache-2.0
"""The environment fingerprint: which machine and which software produced a result (PLAN §7).

Graded results and `benchtop doctor --json` embed it, so a number can be traced back to the operating system,
Python, package versions and commit that produced it. It never holds user names, host names, paths or tokens.
"""

import os
import platform
import shutil
import subprocess
from collections.abc import Mapping
from importlib import metadata
from pathlib import Path
from typing import Final, Literal

import psutil
from pydantic import BaseModel, ConfigDict

__all__ = ["FINGERPRINT_PACKAGES", "EnvironmentFingerprint", "collect_fingerprint", "git_commit"]

FINGERPRINT_PACKAGES: Final = (
    "benchtop-core",
    "benchtop-sim",
    "benchtop-grade",
    "benchtop-data",
    "benchtop-real",
    "benchtop-lab",
    "lerobot",
    "torch",
    "torchvision",
    "mujoco",
    "gymnasium",
    "numpy",
)
"""The packages whose versions decide whether two runs are comparable."""

_GIT_TIMEOUT_S: Final = 5.0


class EnvironmentFingerprint(BaseModel):
    """Machine and software facts recorded with every result.

    Attributes:
        schema_version: Version of this model; bumped with a migration when fields change.
        os: Operating system name, e.g. `Linux`, `Darwin` or `Windows`.
        os_release: Kernel or OS release string.
        machine: CPU architecture, e.g. `x86_64` or `arm64`.
        python: Python version, e.g. `3.12.16`.
        python_implementation: Usually `CPython`.
        cpu: Processor description (may be empty on some Linux systems).
        cpu_count: Logical CPU count.
        ram_gb: Installed memory in GiB, rounded to one decimal.
        torch_device: The device PyTorch would use (`cpu`, `cuda` or `mps`), or `None` if not probed.
        gpu: Name of the CUDA device, or `None`.
        mujoco_gl: Value of `MUJOCO_GL`, or `None` if unset.
        packages: Package name → installed version; packages that are not installed are left out.
        git_commit: Commit of the repository the command ran in, or `None` outside a git checkout.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[1] = 1
    os: str
    os_release: str
    machine: str
    python: str
    python_implementation: str
    cpu: str
    cpu_count: int
    ram_gb: float
    torch_device: str | None
    gpu: str | None
    mujoco_gl: str | None
    packages: dict[str, str]
    git_commit: str | None


def git_commit(cwd: Path | None = None) -> str | None:
    """Return the current git commit hash, or `None` when git or a repository is not available.

    Args:
        cwd: Folder to look in. Defaults to the current working directory.

    Returns:
        The full commit hash of `HEAD`, or `None`.
    """
    git = shutil.which("git")
    if git is None:
        return None
    try:
        result = subprocess.run(
            [git, "rev-parse", "HEAD"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            timeout=_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    commit = result.stdout.strip()
    return commit if result.returncode == 0 and commit else None


def _package_versions() -> dict[str, str]:
    versions: dict[str, str] = {}
    for name in FINGERPRINT_PACKAGES:
        try:
            versions[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            continue
    return versions


def collect_fingerprint(
    *, cwd: Path | None = None, env: Mapping[str, str] | None = None, probe_torch: bool = True
) -> EnvironmentFingerprint:
    """Collect the fingerprint of the current environment.

    Args:
        cwd: Folder whose git commit is recorded. Defaults to the current working directory.
        env: Environment to read `MUJOCO_GL` from. Defaults to `os.environ`.
        probe_torch: Import PyTorch to record the device and GPU name (takes about a second). With `False`,
            `torch_device` and `gpu` are `None`.

    Returns:
        The fingerprint. Collecting it never raises for a missing or broken optional component.
    """
    environment = os.environ if env is None else env
    device: str | None = None
    gpu: str | None = None
    if probe_torch:
        from benchtop_core.compat import torch_info  # noqa: PLC0415  (lazy: keeps this module cheap to import)

        try:
            info = torch_info()
        except (ImportError, OSError, RuntimeError):
            pass
        else:
            device, gpu = info.device, info.cuda_device
    return EnvironmentFingerprint(
        os=platform.system(),
        os_release=platform.release(),
        machine=platform.machine(),
        python=platform.python_version(),
        python_implementation=platform.python_implementation(),
        cpu=platform.processor(),
        cpu_count=os.cpu_count() or 1,
        ram_gb=round(psutil.virtual_memory().total / 2**30, 1),
        torch_device=device,
        gpu=gpu,
        mujoco_gl=environment.get("MUJOCO_GL") or None,
        packages=_package_versions(),
        git_commit=git_commit(cwd),
    )
