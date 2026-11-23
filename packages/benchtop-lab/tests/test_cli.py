# SPDX-FileCopyrightText: 2026 Benchtop Lab contributors
# SPDX-License-Identifier: Apache-2.0
"""Tests for the `benchtop` CLI entry point and its console theme."""

import io
import re
import runpy
import shutil
import subprocess
import sys

import pytest
from typer.testing import CliRunner

from benchtop_lab import __version__
from benchtop_lab.cli import app, main
from benchtop_lab.console import STATUS_GLYPHS, THEME, make_console

ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
runner = CliRunner()


@pytest.mark.parametrize("flag", ["--version", "-V"])
def test_version_flag_prints_version_and_exits_zero(flag: str) -> None:
    result = runner.invoke(app, [flag])
    assert result.exit_code == 0
    assert result.stdout.strip() == f"benchtop {__version__}"


def test_no_arguments_shows_help() -> None:
    result = runner.invoke(app, [])
    # Click exits with status 2 when it shows help because no command was given.
    assert result.exit_code == 2
    assert "Usage" in result.output
    assert "--version" in result.output


def test_help_describes_the_tool() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "SO-101" in result.stdout


def test_unknown_command_fails_with_usage_error() -> None:
    result = runner.invoke(app, ["no-such-command"])
    assert result.exit_code == 2
    assert "No such command" in result.output


def test_main_runs_the_app(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(sys, "argv", ["benchtop", "--version"])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0
    assert capsys.readouterr().out.strip() == f"benchtop {__version__}"


def test_python_dash_m_runs_the_app(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "argv", ["benchtop", "--version"])
    with pytest.raises(SystemExit) as exc:
        runpy.run_module("benchtop_lab", run_name="__main__")
    assert exc.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_installed_console_script_prints_version() -> None:
    exe = shutil.which("benchtop")
    if exe is None:  # pragma: no cover - only when the package is not installed into the venv
        pytest.skip("`benchtop` console script is not on PATH; run `uv sync --all-packages`")
    out = subprocess.run([exe, "--version"], capture_output=True, text=True, check=True, timeout=60)
    assert out.stdout.strip() == f"benchtop {__version__}"


def test_no_color_output_has_no_ansi_codes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.delenv("FORCE_COLOR", raising=False)
    result = runner.invoke(app, ["--version"], color=False)
    assert not ANSI.search(result.output)
    buf = io.StringIO()
    make_console(file=buf).print("[success]✓ Pass[/success] [error]✕ Fail[/error] [accent]benchtop[/accent]")
    assert buf.getvalue() == "✓ Pass ✕ Fail benchtop\n"


def test_no_color_beats_force_color_for_colours(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.setenv("FORCE_COLOR", "1")
    monkeypatch.setenv("TERM", "xterm-256color")
    buf = io.StringIO()
    make_console(file=buf).print("[success]ok[/success] [error]bad[/error]")
    colour_codes = [c for c in ANSI.findall(buf.getvalue()) if re.search(r"\[(3|4|9|10)\d", c)]
    assert colour_codes == []


def test_non_tty_output_is_plain_text() -> None:
    buf = io.StringIO()
    make_console(file=buf).print("[warning]▲ check[/warning]")
    assert buf.getvalue() == "▲ check\n"


def test_forced_colour_uses_the_semantic_theme(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.setenv("FORCE_COLOR", "1")
    monkeypatch.setenv("TERM", "xterm-256color")
    buf = io.StringIO()
    console = make_console(file=buf)
    console.print("[error]x[/error]")
    assert ANSI.search(buf.getvalue())


def test_theme_defines_exactly_the_semantic_styles() -> None:
    names = {"success", "warning", "error", "muted", "accent"}
    assert names <= set(THEME.styles)
    assert set(STATUS_GLYPHS.values()) == {"✓", "▲", "✕", "•"}
