# SPDX-FileCopyrightText: 2026 Benchtop Lab contributors
# SPDX-License-Identifier: Apache-2.0
"""Repository tooling invariants: Makefile targets, pytest markers and licensing files stay in place."""

import re
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
MARKERS = ("slow", "render", "network", "gpu", "hardware")


@pytest.mark.parametrize("target", ["setup", "lint", "type", "test", "test-all", "docs"])
def test_makefile_has_required_target(target: str) -> None:
    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert re.search(rf"^{re.escape(target)}:", makefile, flags=re.MULTILINE)


def test_every_marker_is_registered_and_deselected_by_default() -> None:
    opts = PYPROJECT["tool"]["pytest"]["ini_options"]
    registered = {line.split(":", 1)[0] for line in opts["markers"]}
    assert set(MARKERS) <= registered
    expression = opts["addopts"][opts["addopts"].index("-m") + 1]
    for marker in MARKERS:
        assert f"not {marker}" in expression


def test_licence_texts_for_reuse_exist() -> None:
    for spdx in ("Apache-2.0", "CC-BY-4.0"):
        assert (ROOT / "LICENSES" / f"{spdx}.txt").is_file()
    assert (ROOT / "REUSE.toml").is_file()


def test_lerobot_and_torch_are_forbidden_outside_the_boundary() -> None:
    linter = PYPROJECT["tool"]["importlinter"]
    contracts = {c["id"]: c for c in linter["contracts"]}
    assert linter["include_external_packages"] is True
    assert {"lerobot", "torch"} <= set(contracts["sim-standalone"]["forbidden_modules"])
    boundary = contracts["lerobot-boundary"]
    assert {"lerobot", "torch"} <= set(boundary["forbidden_modules"])
    allowed_sources = {rule.split(" -> ")[0].removesuffix(".**") for rule in boundary["ignore_imports"]}
    assert allowed_sources == {"benchtop_core.compat", "benchtop_core.policies"}


@pytest.mark.parametrize("package", ["core", "sim", "grade", "data", "real", "lab"])
def test_package_licence_is_a_real_copy_of_the_root_licence(package: str) -> None:
    # Regression: symlinked LICENSE files made `uv build` fail ("symbolic-link target escapes the root").
    licence = ROOT / "packages" / f"benchtop-{package}" / "LICENSE"
    assert not licence.is_symlink()
    assert licence.read_bytes() == (ROOT / "LICENSE").read_bytes()


def test_test_file_names_are_unique_across_the_repo() -> None:
    # Test directories have no __init__.py, so mypy and pytest identify test modules by file name alone.
    names = [p.name for p in ROOT.glob("packages/*/tests/**/*.py")] + [
        p.name for p in ROOT.glob("tests/**/*.py")
    ]
    duplicates = sorted({n for n in names if names.count(n) > 1} - {"__init__.py"})
    # A second conftest.py also collides; then configure mypy `explicit_package_bases` instead of renaming.
    hint = (
        "enable mypy `explicit_package_bases` (conftest.py cannot be renamed)"
        if "conftest.py" in duplicates
        else "rename these test files so each name is unique"
    )
    assert duplicates == [], f"{hint}: {duplicates}"
