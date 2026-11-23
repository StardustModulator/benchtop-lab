# SPDX-FileCopyrightText: 2026 Benchtop Lab contributors
# SPDX-License-Identifier: Apache-2.0
"""Console output for the `benchtop` CLI: one semantic theme, shared by every command.

Commands never use raw colours. They print with the semantic styles defined in `THEME` (`success`, `warning`,
`error`, `muted`, `accent`), so the palette can change in one place. `make_console` follows the conventions
learners expect: any non-empty `NO_COLOR` removes every ANSI code (colour and emphasis), `FORCE_COLOR` forces
styling unless it is `0`/`false`, non-TTY output is plain text (no spinners), and the terminal width is
respected.
The styles use ANSI base colours so they stay readable on both light and dark terminal themes.
"""

import os
from collections.abc import Mapping
from typing import IO

from rich.console import Console
from rich.theme import Theme

__all__ = ["STATUS_GLYPHS", "THEME", "make_console"]

THEME = Theme(
    {
        "success": "green",
        "warning": "yellow",
        "error": "bold red",
        "muted": "dim",
        "accent": "bold blue",
    },
    inherit=True,
)
"""Semantic styles. Status is never colour-only: pair each style with a `STATUS_GLYPHS` glyph and a word."""

STATUS_GLYPHS = {"success": "✓", "warning": "▲", "error": "✕", "info": "•"}
"""The only glyphs the CLI uses for status (ui-excellence skill §4)."""


def _no_color(env: Mapping[str, str]) -> bool:
    # https://no-color.org: any non-empty value disables colour.
    return bool(env.get("NO_COLOR"))


def _force_terminal(env: Mapping[str, str]) -> bool | None:
    # Rich treats any FORCE_COLOR value, even "0", as "force"; we follow the common convention instead.
    value = env.get("FORCE_COLOR")
    if value is None or value == "":
        return None
    return value.strip().lower() not in {"0", "false", "no", "off"}


def make_console(
    file: IO[str] | None = None, *, stderr: bool = False, env: Mapping[str, str] | None = None
) -> Console:
    """Create a console with the Benchtop Lab theme.

    Args:
        file: Stream to write to. Defaults to standard output (or standard error if `stderr` is true).
        stderr: Write to standard error instead of standard output.
        env: Environment to read `NO_COLOR` and `FORCE_COLOR` from. Defaults to `os.environ`.

    Returns:
        A `rich.console.Console`. With `NO_COLOR` set it writes no ANSI codes at all; otherwise it styles
        output only for terminals (or when `FORCE_COLOR` asks for it) and wraps to the terminal width.
    """
    environ = os.environ if env is None else env
    no_color = _no_color(environ)
    force = False if no_color else _force_terminal(environ)
    return Console(
        file=file,
        stderr=stderr,
        theme=THEME,
        highlight=False,
        force_terminal=force,
        no_color=no_color,
        color_system=None if no_color else "auto",
        _environ=dict(environ),  # Rich reads TERM, COLUMNS, etc. from here; keeps `env` the single source.
    )
