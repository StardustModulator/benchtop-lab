# SPDX-FileCopyrightText: 2026 Benchtop Lab contributors
# SPDX-License-Identifier: Apache-2.0
"""The `benchtop` command-line interface.

Subcommands (`doctor`, `grade`, `demo`, ...) arrive in later sessions; this module owns the application object
and the global options.
"""

from typing import Annotated

import typer

from benchtop_lab import __version__
from benchtop_lab.console import make_console

__all__ = ["app", "main"]

app = typer.Typer(
    name="benchtop",
    help="Benchtop Lab: graded, sim-first robot-learning projects for the SO-101 arm.",
    no_args_is_help=True,
    add_completion=False,
    pretty_exceptions_show_locals=False,
)


def _print_version(value: bool) -> None:
    if value:
        make_console().print(f"[accent]benchtop[/accent] {__version__}")
        raise typer.Exit


@app.callback()
def root(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-V",
            help="Print the Benchtop Lab version and exit.",
            callback=_print_version,
            is_eager=True,
        ),
    ] = False,
) -> None:
    """Benchtop Lab: graded, sim-first robot-learning projects for the SO-101 arm.

    Run `benchtop COMMAND --help` for help on a command.
    """


def main() -> None:
    """Entry point for the `benchtop` console script and `python -m benchtop_lab`."""
    app(prog_name="benchtop")
