# SPDX-FileCopyrightText: 2026 Benchtop Lab contributors
# SPDX-License-Identifier: Apache-2.0
"""Console output for the `benchtop` CLI: one semantic theme, shared by every command.

Commands never use raw colours. They print with the semantic styles defined in `THEME` (`success`, `warning`,
`error`, `muted`, `accent`), so the palette can change in one place. Rich already honours `NO_COLOR`,
`FORCE_COLOR`, non-TTY output (plain text, no spinners) and the terminal width; `make_console` keeps those
defaults.
The styles use ANSI base colours so they stay readable on both light and dark terminal themes.
"""

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


def make_console(file: IO[str] | None = None, *, stderr: bool = False) -> Console:
    """Create a console with the Benchtop Lab theme.

    Args:
        file: Stream to write to. Defaults to standard output (or standard error if `stderr` is true).
        stderr: Write to standard error instead of standard output.

    Returns:
        A `rich.console.Console` that respects `NO_COLOR`, `FORCE_COLOR`, TTY detection and terminal width.
    """
    return Console(file=file, stderr=stderr, theme=THEME, highlight=False)
