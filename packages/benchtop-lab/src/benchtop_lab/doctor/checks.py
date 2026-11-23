# SPDX-FileCopyrightText: 2026 Benchtop Lab contributors
# SPDX-License-Identifier: Apache-2.0
"""The checks behind `benchtop doctor`.

Each `check_*` function is pure: it turns a measured fact into a `CheckResult` with a one-line finding and, when
something is wrong, the command that fixes it. The facts come from a `Probes` object, so tests replace the
machine with fakes and `run_checks` contains no branching of its own.
"""

import json
import os
import platform
import shutil
import subprocess
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from importlib import metadata
from pathlib import Path
from typing import Final, Literal

import psutil
from pydantic import BaseModel, ConfigDict

from benchtop_core.compat import HubLogin, LeRobotVersion, TorchInfo, hub_login, lerobot_version, torch_info
from benchtop_core.fingerprint import EnvironmentFingerprint, collect_fingerprint

__all__ = ["CheckResult", "DoctorReport", "Probes", "RenderOutcome", "Status", "run_checks"]

SYNC: Final = "uv sync --all-packages --all-groups"
MIN_PYTHON: Final = (3, 12)
TESTED_PYTHON: Final = ((3, 12), (3, 13))
GOOD_CPUS: Final = 4
GOOD_RAM_GB: Final = 8.0
GOOD_DISK_GB: Final = 10.0
MIN_DISK_GB: Final = 2.0
MUJOCO_MAJOR: Final = 4
FALLBACK_BACKENDS: Final = ("egl", "osmesa")
RENDER_TIMEOUT_S: Final = 60.0
GL_PACKAGES: Final = "sudo apt-get install -y libegl1 libegl-mesa0 libgl1-mesa-dri libosmesa6"


class Status(StrEnum):
    """Outcome of one check."""

    PASS = "pass"  # noqa: S105  (a status word, not a password)
    WARN = "warn"
    FAIL = "fail"
    SKIP = "skip"


class CheckResult(BaseModel):
    """The outcome of one check.

    Attributes:
        id: Stable identifier, e.g. `mujoco-render`.
        title: Short name shown in the table.
        status: `pass`, `warn`, `fail` or `skip` (an optional feature that is not set up).
        required: Whether a failure of this check makes `benchtop doctor` exit with an error.
        summary: What was found, in one line.
        fix: The next command to run or step to take; `None` when nothing needs doing.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: str
    title: str
    status: Status
    required: bool
    summary: str
    fix: str | None = None


class DoctorReport(BaseModel):
    """Everything `benchtop doctor` found; this is the `--json` output.

    Attributes:
        schema_version: Version of this model.
        ok: `True` when no required check failed.
        results: One entry per check, in display order.
        fingerprint: The environment fingerprint of this machine.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal[1] = 1
    ok: bool
    results: tuple[CheckResult, ...]
    fingerprint: EnvironmentFingerprint

    def count(self, status: Status) -> int:
        """Number of checks with the given status."""
        return sum(result.status is status for result in self.results)

    @property
    def exit_code(self) -> int:
        """`0` when the machine is ready, `1` when a required check failed."""
        return 0 if self.ok else 1


@dataclass(frozen=True, slots=True)
class RenderOutcome:
    """Result of one offscreen render attempt.

    Attributes:
        ok: A non-blank 64 by 64 RGB image was produced.
        detail: The first line of the error, or a description of the image.
    """

    ok: bool
    detail: str


def _pass(check: str, title: str, summary: str, *, required: bool) -> CheckResult:
    return CheckResult(id=check, title=title, status=Status.PASS, required=required, summary=summary)


def _problem(
    check: str, title: str, status: Status, summary: str, fix: str, *, required: bool
) -> CheckResult:
    return CheckResult(id=check, title=title, status=status, required=required, summary=summary, fix=fix)


def _first_line(error: BaseException) -> str:
    text = str(error).strip()
    return text.splitlines()[0] if text else type(error).__name__


def check_python(version: tuple[int, int, int]) -> CheckResult:
    """Python must be 3.12 or newer; 3.12 and 3.13 are the tested versions."""
    text = ".".join(str(part) for part in version)
    if version[:2] < MIN_PYTHON:
        fix = f"uv python install 3.12 && {SYNC}"
        return _problem(
            "python", "Python", Status.FAIL, f"{text}; Benchtop Lab needs 3.12 or newer", fix, required=True
        )
    if version[:2] not in TESTED_PYTHON:
        return _problem(
            "python",
            "Python",
            Status.WARN,
            f"{text}; untested (CI covers 3.12 and 3.13)",
            f"if something breaks: uv python install 3.12 && {SYNC}",
            required=True,
        )
    return _pass("python", "Python", text, required=True)


def check_os(system: str, release: str, machine: str) -> CheckResult:
    """Linux and macOS are tested; Windows works best through WSL 2."""
    summary = f"{system} {release} ({machine})".strip()
    if system in {"Linux", "Darwin"}:
        return _pass("os", "Operating system", summary, required=False)
    if system == "Windows":
        fix = "use WSL 2 (run: wsl --install) and install Benchtop Lab inside it"
        return _problem(
            "os",
            "Operating system",
            Status.WARN,
            f"{summary}; native Windows is untested",
            fix,
            required=False,
        )
    return _problem(
        "os",
        "Operating system",
        Status.WARN,
        f"{summary}; untested platform",
        "use Linux, macOS or WSL 2 if you hit problems",
        required=False,
    )


def check_cpu(count: int | None) -> CheckResult:
    """Four or more logical CPUs keep CPU training and parallel evaluation comfortable."""
    if count is None:
        return _problem(
            "cpu",
            "CPU",
            Status.WARN,
            "could not count CPUs",
            "nothing to do if the machine feels fast",
            required=False,
        )
    if count < GOOD_CPUS:
        return _problem(
            "cpu",
            "CPU",
            Status.WARN,
            f"{count} logical CPUs; training and evaluation will be slow",
            "use the Colab or Kaggle notebooks for the training steps",
            required=False,
        )
    return _pass("cpu", "CPU", f"{count} logical CPUs", required=False)


def check_ram(total_gb: float) -> CheckResult:
    """8 GB of memory or more is comfortable; less works with care."""
    if total_gb < GOOD_RAM_GB:
        return _problem(
            "ram",
            "Memory",
            Status.WARN,
            f"{total_gb:.1f} GB; less than the recommended 8 GB",
            "close other applications while training, or train in a Colab or Kaggle notebook",
            required=False,
        )
    return _pass("ram", "Memory", f"{total_gb:.1f} GB", required=False)


def check_disk(free_gb: float) -> CheckResult:
    """Datasets, checkpoints and videos need free disk space where the command runs.

    The folder itself is not named: learners paste this output into issues, and paths often hold a user name.
    """
    where = "free in the current folder"
    if free_gb < MIN_DISK_GB:
        return _problem(
            "disk",
            "Disk space",
            Status.FAIL,
            f"{free_gb:.1f} GB {where}; datasets and checkpoints will not fit",
            "free at least 10 GB (clear old runs with: rm -r outputs/, or run: uv cache clean)",
            required=True,
        )
    if free_gb < GOOD_DISK_GB:
        return _problem(
            "disk",
            "Disk space",
            Status.WARN,
            f"{free_gb:.1f} GB {where}; less than the recommended 10 GB",
            "free some space before recording datasets or training",
            required=True,
        )
    return _pass("disk", "Disk space", f"{free_gb:.1f} GB {where}", required=True)


def check_mujoco(version: str | None, error: str | None = None) -> CheckResult:
    """MuJoCo must import and be a 4.x release."""
    if version is None:
        return _problem(
            "mujoco",
            "MuJoCo",
            Status.FAIL,
            f"cannot be imported ({error or 'not installed'})",
            SYNC,
            required=True,
        )
    if version.split(".")[0] != str(MUJOCO_MAJOR):
        return _problem(
            "mujoco",
            "MuJoCo",
            Status.WARN,
            f"{version}; Benchtop Lab is tested with 4.x",
            SYNC,
            required=True,
        )
    return _pass("mujoco", "MuJoCo", version, required=True)


def check_render(
    backend: str | None, outcome: RenderOutcome, working_fallback: str | None, system: str
) -> CheckResult:
    """A 64 by 64 test scene must render offscreen with the active `MUJOCO_GL` backend."""
    active = backend or "default"
    title = "Offscreen rendering"
    if outcome.ok:
        return _pass("mujoco-render", title, f"MUJOCO_GL={active}; 64×64 test scene rendered", required=True)
    summary = f"MUJOCO_GL={active} failed ({outcome.detail})"
    if working_fallback is not None:
        fix = f"export MUJOCO_GL={working_fallback}   (this backend works on this machine)"
    elif system == "Linux":
        fix = f"{GL_PACKAGES} && export MUJOCO_GL=egl"
    elif system == "Darwin":
        fix = f"unset MUJOCO_GL   (macOS uses its own OpenGL), then: {SYNC}"
    else:
        fix = "update the graphics driver, or use WSL 2 with: export MUJOCO_GL=egl"
    return _problem("mujoco-render", title, Status.FAIL, summary, fix, required=True)


def check_lerobot(found: LeRobotVersion) -> CheckResult:
    """LeRobot must be installed and inside the supported range."""
    if found.installed is None:
        return _problem("lerobot", "LeRobot", Status.FAIL, "not installed", SYNC, required=True)
    if not found.supported:
        return _problem(
            "lerobot",
            "LeRobot",
            Status.FAIL,
            f"{found.installed}; Benchtop Lab supports lerobot{found.required}",
            SYNC,
            required=True,
        )
    return _pass("lerobot", "LeRobot", f"{found.installed} (supported: {found.required})", required=True)


def check_ffmpeg(path: str | None, system: str) -> CheckResult:
    """The `ffmpeg` command is optional: LeRobot encodes video through its bundled PyAV."""
    if path is None:
        install = "brew install ffmpeg" if system == "Darwin" else "sudo apt-get install -y ffmpeg"
        return _problem(
            "ffmpeg",
            "ffmpeg",
            Status.WARN,
            "command not found; datasets still work, some video tools will not",
            install,
            required=False,
        )
    return _pass("ffmpeg", "ffmpeg", "available", required=False)


def check_torch(info: TorchInfo | None, error: str | None = None) -> CheckResult:
    """PyTorch must import; any device is fine because the curriculum is CPU-first (ADR-005)."""
    if info is None:
        return _problem(
            "torch",
            "PyTorch",
            Status.FAIL,
            f"cannot be imported ({error or 'not installed'})",
            f"{SYNC} --extra cpu",
            required=True,
        )
    if info.cuda_available:
        device = f"CUDA ({info.cuda_device or 'GPU'})"
    elif info.mps_available:
        device = "MPS (Apple GPU)"
    else:
        device = "CPU (no GPU found; the core projects are sized for CPU)"
    return _pass("torch", "PyTorch", f"{info.version}; device: {device}", required=True)


def check_hub_login(login: HubLogin | None) -> CheckResult:
    """A Hugging Face login is optional; only its presence is reported, never the token."""
    title = "Hugging Face login"
    if login is not None and login.logged_in:
        return _pass("hf-login", title, "token found (not shown)", required=False)
    return CheckResult(
        id="hf-login",
        title=title,
        status=Status.SKIP,
        required=False,
        summary="not logged in; optional, public datasets and models need no account",
        fix="only for private or gated repositories: hf auth login",
    )


def _python_version() -> tuple[int, int, int]:
    return (sys.version_info.major, sys.version_info.minor, sys.version_info.micro)


def _ram_gb() -> float:
    return float(psutil.virtual_memory().total) / 2**30


def _disk_free_gb(path: Path) -> float:
    return shutil.disk_usage(path).free / 2**30


def _mujoco_version() -> str:
    return metadata.version("mujoco")


def render_in_subprocess(backend: str | None, env: Mapping[str, str] | None = None) -> RenderOutcome:
    """Render the test scene in a child process with the given `MUJOCO_GL` backend.

    Args:
        backend: Value for `MUJOCO_GL`; `None` leaves MuJoCo's platform default.
        env: Base environment. Defaults to `os.environ`.

    Returns:
        Whether a non-blank image was rendered, and the first line of the error otherwise.
    """
    child_env = dict(os.environ if env is None else env)
    child_env.pop("MUJOCO_GL", None)
    if backend:
        child_env["MUJOCO_GL"] = backend
    command = [sys.executable, "-m", "benchtop_lab.doctor.render_probe"]
    try:
        done = subprocess.run(
            command, env=child_env, capture_output=True, text=True, check=False, timeout=RENDER_TIMEOUT_S
        )
    except subprocess.TimeoutExpired:
        return RenderOutcome(ok=False, detail=f"no image after {RENDER_TIMEOUT_S:.0f} s")
    except OSError as error:
        return RenderOutcome(ok=False, detail=_first_line(error))
    lines = done.stdout.strip().splitlines()
    try:
        result = json.loads(lines[-1]) if lines else None
    except json.JSONDecodeError:
        result = None
    if not isinstance(result, dict):
        return RenderOutcome(ok=False, detail=f"the renderer stopped with exit code {done.returncode}")
    if result.get("ok") is True and done.returncode == 0:
        return RenderOutcome(ok=True, detail="rendered")
    if "error" in result:
        return RenderOutcome(ok=False, detail=str(result["error"]))
    return RenderOutcome(ok=False, detail="the image was blank or had the wrong shape")


@dataclass(frozen=True, slots=True)
class Probes:
    """Where the checks get their facts. Tests replace individual probes with fakes.

    Attributes:
        env: The environment (`MUJOCO_GL` is read from it).
        cwd: The folder whose disk space and git commit are reported.
        python_version: Returns the running Python version.
        system: Returns the OS name (`Linux`, `Darwin`, `Windows`).
        release: Returns the OS release.
        machine: Returns the CPU architecture.
        cpu_count: Returns the logical CPU count, or `None`.
        ram_gb: Returns installed memory in GiB.
        disk_free_gb: Returns free space in GiB for a folder.
        mujoco_version: Returns the installed MuJoCo version; raises if it is missing.
        render: Renders the test scene with a `MUJOCO_GL` backend.
        lerobot: Returns the installed LeRobot version and range.
        which: Finds an executable on `PATH`.
        torch: Returns PyTorch facts; raises if PyTorch cannot be imported.
        hub_login: Returns the Hugging Face login state; raises if `huggingface_hub` is missing.
        fingerprint: Collects the environment fingerprint.
    """

    env: Mapping[str, str] = field(default_factory=lambda: os.environ)
    cwd: Path = field(default_factory=Path.cwd)
    python_version: Callable[[], tuple[int, int, int]] = _python_version
    system: Callable[[], str] = platform.system
    release: Callable[[], str] = platform.release
    machine: Callable[[], str] = platform.machine
    cpu_count: Callable[[], int | None] = os.cpu_count
    ram_gb: Callable[[], float] = _ram_gb
    disk_free_gb: Callable[[Path], float] = _disk_free_gb
    mujoco_version: Callable[[], str] = _mujoco_version
    render: Callable[[str | None], RenderOutcome] = render_in_subprocess
    lerobot: Callable[[], LeRobotVersion] = lerobot_version
    which: Callable[[str], str | None] = shutil.which
    torch: Callable[[], TorchInfo] = torch_info
    hub_login: Callable[[], HubLogin] = hub_login
    fingerprint: Callable[[], EnvironmentFingerprint] = collect_fingerprint


def _mujoco_and_render(probes: Probes, system: str) -> tuple[CheckResult, CheckResult]:
    try:
        version = probes.mujoco_version()
    except (ImportError, metadata.PackageNotFoundError, OSError) as error:
        missing = check_mujoco(None, _first_line(error))
        skipped = CheckResult(
            id="mujoco-render",
            title="Offscreen rendering",
            status=Status.FAIL,
            required=True,
            summary="not tried because MuJoCo is missing",
            fix=SYNC,
        )
        return missing, skipped
    backend = probes.env.get("MUJOCO_GL") or None
    outcome = probes.render(backend)
    fallback: str | None = None
    if not outcome.ok and system == "Linux":
        candidates = (name for name in FALLBACK_BACKENDS if name != backend)
        fallback = next((name for name in candidates if probes.render(name).ok), None)
    return check_mujoco(version), check_render(backend, outcome, fallback, system)


def run_checks(probes: Probes | None = None) -> DoctorReport:
    """Run every check and collect the report.

    Args:
        probes: Where to read the machine's facts from. Defaults to the real machine.

    Returns:
        The report, with one result per check in display order. `ok` is `False` when a required check failed.
    """
    probes = probes or Probes()
    system = probes.system()
    mujoco_result, render_result = _mujoco_and_render(probes, system)
    try:
        torch_result = check_torch(probes.torch())
    except (ImportError, OSError, RuntimeError) as error:
        torch_result = check_torch(None, _first_line(error))
    try:
        login: HubLogin | None = probes.hub_login()
    except (ImportError, OSError):
        login = None
    results = (
        check_python(probes.python_version()),
        check_os(system, probes.release(), probes.machine()),
        check_cpu(probes.cpu_count()),
        check_ram(probes.ram_gb()),
        check_disk(probes.disk_free_gb(probes.cwd)),
        mujoco_result,
        render_result,
        check_lerobot(probes.lerobot()),
        torch_result,
        check_ffmpeg(probes.which("ffmpeg"), system),
        check_hub_login(login),
    )
    ok = not any(result.required and result.status is Status.FAIL for result in results)
    return DoctorReport(ok=ok, results=results, fingerprint=probes.fingerprint())
