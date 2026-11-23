# SPDX-FileCopyrightText: 2026 Benchtop Lab contributors
# SPDX-License-Identifier: Apache-2.0
"""Make CLI tests independent of the colour settings of the machine running them."""

import os
from collections.abc import Iterator

import pytest
import typer.rich_utils

from benchtop_lab.console import configure_help_output

COLOUR_VARIABLES = (
    "NO_COLOR",
    "FORCE_COLOR",
    "GITHUB_ACTIONS",
    "PY_COLORS",
    "TERM",
    "COLUMNS",
    "TERMINAL_WIDTH",
)


@pytest.fixture(autouse=True)
def neutral_terminal_environment(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Remove colour variables (CI and some runners set them) and reset Typer's import-time globals."""
    for name in COLOUR_VARIABLES:
        monkeypatch.delenv(name, raising=False)
    saved = (typer.rich_utils.FORCE_TERMINAL, typer.rich_utils.COLOR_SYSTEM)
    configure_help_output(os.environ)
    yield
    typer.rich_utils.FORCE_TERMINAL, typer.rich_utils.COLOR_SYSTEM = saved
