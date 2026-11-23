# SPDX-FileCopyrightText: 2026 Benchtop Lab contributors
# SPDX-License-Identifier: Apache-2.0
"""The environment fingerprint is complete, serialisable and free of personal data."""

import getpass
import json
import platform
import shutil
import socket
import subprocess
from importlib import metadata
from pathlib import Path

import pytest
from pydantic import ValidationError

from benchtop_core import compat
from benchtop_core.fingerprint import EnvironmentFingerprint, collect_fingerprint, git_commit


def test_collects_machine_and_software_facts() -> None:
    found = collect_fingerprint(env={"MUJOCO_GL": "egl"}, probe_torch=False)
    assert found.schema_version == 1
    assert found.os == platform.system()
    assert found.python == platform.python_version()
    assert found.cpu_count >= 1
    assert found.ram_gb > 0
    assert found.mujoco_gl == "egl"
    assert (found.torch_device, found.gpu) == (None, None)
    for name in ("benchtop-core", "lerobot", "torch", "mujoco", "numpy", "gymnasium"):
        assert found.packages[name] == metadata.version(name)


def test_records_the_torch_device_when_probed(monkeypatch: pytest.MonkeyPatch) -> None:
    info = compat.TorchInfo(
        "2.15.0", cuda_available=True, cuda_device="Test GPU", mps_available=False, device="cuda"
    )
    monkeypatch.setattr(compat, "torch_info", lambda: info)
    found = collect_fingerprint(env={})
    assert (found.torch_device, found.gpu, found.mujoco_gl) == ("cuda", "Test GPU", None)


def test_a_broken_torch_does_not_break_the_fingerprint(monkeypatch: pytest.MonkeyPatch) -> None:
    def broken() -> compat.TorchInfo:
        raise ImportError("libtorch.so: cannot open shared object file")

    monkeypatch.setattr(compat, "torch_info", broken)
    assert collect_fingerprint(env={}).torch_device is None


def test_packages_that_are_not_installed_are_left_out(monkeypatch: pytest.MonkeyPatch) -> None:
    real_version = metadata.version

    def fake_version(name: str) -> str:
        if name == "torchvision":
            raise metadata.PackageNotFoundError(name)
        return real_version(name)

    monkeypatch.setattr(metadata, "version", fake_version)
    packages = collect_fingerprint(env={}, probe_torch=False).packages
    assert "torchvision" not in packages
    assert "torch" in packages


def test_round_trips_through_json_and_rejects_unknown_fields() -> None:
    found = collect_fingerprint(env={}, probe_torch=False)
    data = json.loads(found.model_dump_json())
    assert EnvironmentFingerprint.model_validate(data) == found
    with pytest.raises(ValidationError):
        EnvironmentFingerprint.model_validate({**data, "hostname": "lab-pc"})
    with pytest.raises(ValidationError):
        found.os = "Plan 9"


def test_contains_no_user_name_host_name_or_home_path(tmp_path: Path) -> None:
    text = collect_fingerprint(
        cwd=tmp_path, env={"HF_TOKEN": "hf_secret", "MUJOCO_GL": "egl"}
    ).model_dump_json()
    assert "hf_secret" not in text
    assert str(Path.home()) not in text
    host = socket.gethostname()
    if len(host) > 3:
        assert host not in text
    user = getpass.getuser()
    if len(user) > 3:
        assert f'"{user}"' not in text


def test_git_commit_of_a_repository(tmp_path: Path) -> None:
    executable = shutil.which("git")
    assert executable, "git is required for this test"

    def git(*args: str) -> str:
        done = subprocess.run([executable, *args], cwd=tmp_path, capture_output=True, text=True, check=True)
        return done.stdout.strip()

    git("init", "-q")
    git("-c", "user.name=T", "-c", "user.email=t@example.com", "commit", "-q", "--allow-empty", "-m", "x")
    assert git_commit(tmp_path) == git("rev-parse", "HEAD")
    assert collect_fingerprint(cwd=tmp_path, env={}, probe_torch=False).git_commit == git("rev-parse", "HEAD")


def test_git_commit_outside_a_repository_or_without_git(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    assert git_commit(tmp_path) is None
    monkeypatch.setattr(shutil, "which", lambda name: None)
    assert git_commit(Path.cwd()) is None


def test_git_commit_survives_a_git_that_cannot_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(shutil, "which", lambda name: str(tmp_path / "missing-git"))
    assert git_commit(tmp_path) is None
