# SPDX-FileCopyrightText: 2026 Benchtop Lab contributors
# SPDX-License-Identifier: Apache-2.0
"""Smoke test: `benchtop_lab` imports, is typed, and reports the installed version."""

from importlib.metadata import version
from importlib.resources import files

import benchtop_lab


def test_imports_and_reports_installed_version() -> None:
    assert benchtop_lab.__version__ == version("benchtop-lab")


def test_ships_py_typed_marker() -> None:
    assert files("benchtop_lab").joinpath("py.typed").is_file()
