# SPDX-FileCopyrightText: 2026 Benchtop Lab contributors
# SPDX-License-Identifier: Apache-2.0
"""Console output for the `benchtop` CLI: one semantic theme, shared by every command.

Commands never use raw colours. They print with the semantic styles defined in `THEME` (`success`, `warning`,
`error`, `muted`, `accent`), so the palette can change in one place. Colour behaviour follows the conventions
learners expect and is decided in one pure function, `colour_settings`, used both by `make_console` and by the
Typer help screens (`configure_help_output`):

- any non-empty `NO_COLOR` removes every ANSI code, colour and emphasis alike (https://no-color.org);
- `FORCE_COLOR` forces styling unless it is `0`, `false`, `no` or `off` (Rich and Typer alone treat any value,
  even `0`, as "on");
- otherwise output is styled only on a real terminal; pipes and files get plain text with no spinners.

The styles use bold and the green/yellow/red base colours, which stay readable on light and dark terminal
themes.
"""

import os
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import IO, Final

import typer.rich_utils
from rich.console import Console
from rich.theme import Theme

__all__ = [
    "STATUS_GLYPHS",
    "THEME",
    "ColourSettings",
    "colour_settings",
    "configure_help_output",
    "make_console",
]

THEME: Final = Theme(
    {
        "success": "green",
        "warning": "yellow",
        "error": "bold red",
        "muted": "dim",
        "accent": "bold",
    },
    inherit=True,
)
"""Semantic styles. Status is never colour-only: pair each style with a `STATUS_GLYPHS` glyph and a word."""

STATUS_GLYPHS: Final[Mapping[str, str]] = MappingProxyType(
    {"success": "✓", "warning": "▲", "error": "✕", "info": "•"}
)
"""The only glyphs the CLI uses for status (ui-excellence skill §4)."""

_FALSE_WORDS: Final = frozenset({"0", "false", "no", "off"})


@dataclass(frozen=True, slots=True)
class ColourSettings:
    """How a console should style its output.

    Attributes:
        no_color: Strip every ANSI code.
        force_terminal: `True` to style even when not writing to a terminal, `False` to never style, `None` to
            detect a terminal.
    """

    no_color: bool
    force_terminal: bool | None


def colour_settings(env: Mapping[str, str]) -> ColourSettings:
    """Decide colour behaviour from `NO_COLOR` and `FORCE_COLOR`.

    Args:
        env: The environment, usually `os.environ`.

    Returns:
        The settings for every Benchtop Lab console. `NO_COLOR` always wins over `FORCE_COLOR`.
    """
    if env.get("NO_COLOR"):
        return ColourSettings(no_color=True, force_terminal=False)
    force = env.get("FORCE_COLOR")
    if force is None or force.strip() == "":
        return ColourSettings(no_color=False, force_terminal=None)
    return ColourSettings(no_color=False, force_terminal=force.strip().lower() not in _FALSE_WORDS)


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
    settings = colour_settings(os.environ if env is None else env)
    return Console(
        file=file,
        stderr=stderr,
        theme=THEME,
        highlight=False,
        force_terminal=settings.force_terminal,
        no_color=settings.no_color,
        color_system=None if settings.no_color else "auto",
    )


def configure_help_output(env: Mapping[str, str]) -> None:
    """Apply `colour_settings` to Typer's help and error screens.

    Typer builds its own Rich console from module globals that it computes once at import time (and it treats
    `FORCE_COLOR=0` and `GITHUB_ACTIONS` as "force colour"). Call this before running the app so help output
    follows the same rules as `make_console`.

    Args:
        env: The environment, usually `os.environ`.
    """
    settings = colour_settings(env)
    typer.rich_utils.FORCE_TERMINAL = settings.force_terminal
    typer.rich_utils.COLOR_SYSTEM = None if settings.no_color else "auto"
