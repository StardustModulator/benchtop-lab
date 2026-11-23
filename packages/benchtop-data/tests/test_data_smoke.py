# SPDX-FileCopyrightText: 2026 Benchtop Lab contributors
# SPDX-License-Identifier: Apache-2.0
"""Smoke test: `benchtop_data` imports, is typed, and reports the installed version."""

from importlib.metadata import version
from importlib.resources import files

import benchtop_data


def test_imports_and_reports_installed_version() -> None:
    assert benchtop_data.__version__ == version("benchtop-data")


def test_ships_py_typed_marker() -> None:
    assert files("benchtop_data").joinpath("py.typed").is_file()
