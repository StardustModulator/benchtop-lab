# SPDX-FileCopyrightText: 2026 Benchtop Lab contributors
# SPDX-License-Identifier: Apache-2.0
"""MkDocs hooks for the Benchtop Lab docs site (registered under `hooks:` in mkdocs.yml).

The command-line reference is rendered from the installed `benchtop` application at build time, so the page
cannot drift from the code.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import click
import typer.main
from typer.testing import CliRunner

if TYPE_CHECKING:
    from collections.abc import Iterator

CLI_MARKER = "<!-- benchtop:cli-reference -->"
HELP_WIDTH = 88
# Plain text at a fixed width, whatever terminal or CI system runs the build.
HELP_ENV = {"NO_COLOR": "1", "FORCE_COLOR": "0", "TERM": "dumb", "COLUMNS": str(HELP_WIDTH)}


def iter_commands(command: click.Command, path: tuple[str, ...] = ()) -> Iterator[tuple[str, ...]]:
    """Yield the argument path of `command` and of every visible subcommand, depth first, in help order."""
    yield path
    if isinstance(command, click.Group):
        for name, sub in command.commands.items():
            if not sub.hidden:
                yield from iter_commands(sub, (*path, name))


def help_text(app: typer.Typer, path: tuple[str, ...], prog_name: str) -> str:
    """Return the `--help` output of the command at `path`, as plain text without trailing spaces."""
    result = CliRunner().invoke(
        app, [*path, "--help"], prog_name=prog_name, env=HELP_ENV, terminal_width=HELP_WIDTH
    )
    if result.exit_code != 0:
        command = " ".join((prog_name, *path))
        message = f"`{command} --help` exited with code {result.exit_code}; fix the command before building the docs."
        raise RuntimeError(message)
    lines = [line.rstrip() for line in result.output.splitlines()]
    return "\n".join(lines).strip("\n")


def render_cli_reference(app: typer.Typer, prog_name: str = "benchtop") -> str:
    """Render one Markdown section per command: a heading and the command's help in a text block."""
    sections = []
    for path in iter_commands(typer.main.get_command(app)):
        command = " ".join((prog_name, *path))
        level = "#" * min(3 + max(len(path) - 1, 0), 6)
        sections.append(f"{level} `{command}`\n\n```text\n{help_text(app, path, prog_name)}\n```")
    return "\n\n".join(sections)


def on_page_markdown(markdown: str, **_: Any) -> str:
    """MkDocs event: replace the marker comment with the generated command-line reference."""
    if CLI_MARKER not in markdown:
        return markdown
    from benchtop_lab.cli import app  # noqa: PLC0415  (imported only for the one page that needs it)

    return markdown.replace(CLI_MARKER, render_cli_reference(app))
