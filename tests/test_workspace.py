# SPDX-FileCopyrightText: 2026 Benchtop Lab contributors
# SPDX-License-Identifier: Apache-2.0
"""Cross-package tests: the six workspace packages are installed and released under one shared version."""

import importlib
from importlib.metadata import version

import pytest

PACKAGES = {
    "benchtop-core": "benchtop_core",
    "benchtop-sim": "benchtop_sim",
    "benchtop-grade": "benchtop_grade",
    "benchtop-data": "benchtop_data",
    "benchtop-real": "benchtop_real",
    "benchtop-lab": "benchtop_lab",
}


@pytest.mark.parametrize(("dist", "module"), PACKAGES.items())
def test_package_is_installed_and_importable(dist: str, module: str) -> None:
    mod = importlib.import_module(module)
    assert mod.__version__ == version(dist)


def test_all_packages_share_one_version() -> None:
    versions = {dist: version(dist) for dist in PACKAGES}
    assert len(set(versions.values())) == 1, f"packages must share one version, got {versions}"
