# SPDX-FileCopyrightText: 2026 Benchtop Lab contributors
# SPDX-License-Identifier: Apache-2.0
"""The `benchtop` command-line interface.

This module owns the application object, the global options and the thin command functions. Commands import
their implementation when they run, so `benchtop --help` stays fast (PLAN §11).
"""

import os
from typing import Annotated

import typer

from benchtop_lab import __version__
from benchtop_lab.console import configure_help_output, make_console

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


@app.command()
def doctor(
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Print the full report (checks and environment fingerprint) as JSON."),
    ] = False,
) -> None:
    """Check that this machine can run Benchtop Lab, and show how to fix what cannot.

    Exits with status 1 when a required check fails (Python, disk space, MuJoCo, offscreen rendering, LeRobot,
    PyTorch); warnings and optional checks never change the exit status.
    """
    from benchtop_lab.doctor import print_report, run_checks  # noqa: PLC0415  (lazy: keeps --help fast)

    console = make_console()
    if json_output or not console.is_terminal or console.no_color:
        report = run_checks()
    else:
        with console.status("Checking this machine…"):
            report = run_checks()
    if json_output:
        typer.echo(report.model_dump_json(indent=2))
    else:
        print_report(report, console)
    raise typer.Exit(report.exit_code)


def main() -> None:
    """Entry point for the `benchtop` console script and `python -m benchtop_lab`."""
    configure_help_output(os.environ)
    app(prog_name="benchtop")
