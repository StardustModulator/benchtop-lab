# SPDX-FileCopyrightText: 2026 Benchtop Lab contributors
# SPDX-License-Identifier: Apache-2.0
"""`lerobot_version()` reports the installed LeRobot and checks it against the pinned range."""

import subprocess
import sys
from importlib import metadata

import pytest

from benchtop_core import compat
from benchtop_core.errors import BenchtopError


def _installed(monkeypatch: pytest.MonkeyPatch, version: str | None) -> None:
    real_version = metadata.version

    def fake_version(name: str) -> str:
        if name != "lerobot":
            return real_version(name)
        if version is None:
            raise metadata.PackageNotFoundError(name)
        return version

    monkeypatch.setattr(metadata, "version", fake_version)


def test_reports_the_installed_version_as_supported() -> None:
    found = compat.lerobot_version()
    assert found.installed == metadata.version("lerobot")
    assert found.supported
    assert found.required == str(compat.SUPPORTED_LEROBOT)
    assert compat.require_supported_lerobot() == found


@pytest.mark.parametrize(
    ("version", "supported"),
    [
        ("0.7.0", True),
        ("0.7.3", True),
        ("0.7.1rc1", True),
        ("0.6.9", False),
        ("0.8.0", False),
        ("1.0.0", False),
        ("not-a-version", False),
    ],
)
def test_supported_range(monkeypatch: pytest.MonkeyPatch, version: str, supported: bool) -> None:
    _installed(monkeypatch, version)
    assert compat.lerobot_version().supported is supported


def test_missing_lerobot_is_reported_not_raised(monkeypatch: pytest.MonkeyPatch) -> None:
    _installed(monkeypatch, None)
    found = compat.lerobot_version()
    assert found.installed is None
    assert not found.supported


def test_require_raises_an_actionable_error_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    _installed(monkeypatch, None)
    with pytest.raises(BenchtopError, match="not installed") as caught:
        compat.require_supported_lerobot()
    assert "uv sync" in caught.value.fix


def test_require_raises_an_actionable_error_when_out_of_range(monkeypatch: pytest.MonkeyPatch) -> None:
    _installed(monkeypatch, "0.8.2")
    with pytest.raises(BenchtopError, match=r"LeRobot 0\.8\.2") as caught:
        compat.require_supported_lerobot()
    assert "0.7" in caught.value.what
    assert "uv sync" in caught.value.fix


def test_importing_compat_and_reading_the_version_does_not_import_lerobot_or_torch() -> None:
    """PLAN §11: `benchtop --help` and sim-only commands must not pay for torch."""
    code = (
        "import sys; from benchtop_core import compat; compat.lerobot_version(); "
        "bad = sorted(m for m in ('lerobot', 'torch', 'datasets', 'huggingface_hub') if m in sys.modules); "
        "print(bad); sys.exit(1 if bad else 0)"
    )
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
