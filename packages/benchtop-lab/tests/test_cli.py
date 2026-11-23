# SPDX-FileCopyrightText: 2026 Benchtop Lab contributors
# SPDX-License-Identifier: Apache-2.0
"""Tests for the `benchtop` CLI entry point and its console theme.

`conftest.py` removes colour-related environment variables before every test, so each test sets exactly the
environment it needs.
"""

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
from benchtop_lab.console import STATUS_GLYPHS, THEME, ColourSettings, colour_settings, make_console

ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
runner = CliRunner()


def run_main(
    args: list[str], monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> tuple[int | str | None, str]:
    """Run the real entry point (which configures Typer's help console) and capture its output."""
    monkeypatch.setattr(sys, "argv", ["benchtop", *args])
    with pytest.raises(SystemExit) as exc:
        main()
    return exc.value.code, capsys.readouterr().out


# --- command behaviour


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
    code, out = run_main(["--version"], monkeypatch, capsys)
    assert code == 0
    assert out == f"benchtop {__version__}\n"


def test_python_dash_m_runs_the_app_as_benchtop(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "argv", ["python -m benchtop_lab", "--help"])
    with pytest.raises(SystemExit) as exc:
        runpy.run_module("benchtop_lab", run_name="__main__")
    assert exc.value.code == 0
    assert "Usage: benchtop " in capsys.readouterr().out


def test_installed_console_script_prints_version() -> None:
    exe = shutil.which("benchtop")
    if exe is None:  # pragma: no cover - only when the package is not installed into the venv
        pytest.skip("`benchtop` console script is not on PATH; run `uv sync --all-packages`")
    env = {"PATH": "", "NO_COLOR": "1"}
    out = subprocess.run([exe, "--version"], capture_output=True, text=True, check=True, timeout=60, env=env)
    assert out.stdout == f"benchtop {__version__}\n"


# --- help output follows the same colour rules as make_console


@pytest.mark.parametrize(
    "env",
    [
        {},
        {"FORCE_COLOR": "0"},  # regression: Typer alone treats FORCE_COLOR=0 as "force colour"
        {"GITHUB_ACTIONS": "true"},  # regression: Typer alone forces colour on GitHub Actions
        {"NO_COLOR": "1", "FORCE_COLOR": "1"},
    ],
)
def test_help_piped_to_a_file_is_plain_text(
    env: dict[str, str], monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setenv("TERM", "xterm-256color")
    code, out = run_main(["--help"], monkeypatch, capsys)
    assert code == 0
    assert not ANSI.search(out)
    assert "Usage: benchtop [OPTIONS] COMMAND [ARGS]..." in out


def test_help_is_styled_when_colour_is_forced(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("FORCE_COLOR", "1")
    monkeypatch.setenv("TERM", "xterm-256color")
    _, out = run_main(["--help"], monkeypatch, capsys)
    assert ANSI.search(out)


# --- the colour decision


@pytest.mark.parametrize(
    ("env", "expected"),
    [
        ({}, ColourSettings(no_color=False, force_terminal=None)),
        ({"FORCE_COLOR": ""}, ColourSettings(no_color=False, force_terminal=None)),
        ({"FORCE_COLOR": "1"}, ColourSettings(no_color=False, force_terminal=True)),
        ({"FORCE_COLOR": "true"}, ColourSettings(no_color=False, force_terminal=True)),
        ({"FORCE_COLOR": "0"}, ColourSettings(no_color=False, force_terminal=False)),
        ({"FORCE_COLOR": " OFF "}, ColourSettings(no_color=False, force_terminal=False)),
        ({"NO_COLOR": ""}, ColourSettings(no_color=False, force_terminal=None)),
        ({"NO_COLOR": "1"}, ColourSettings(no_color=True, force_terminal=False)),
        ({"NO_COLOR": "yes", "FORCE_COLOR": "1"}, ColourSettings(no_color=True, force_terminal=False)),
    ],
)
def test_colour_settings(env: dict[str, str], expected: ColourSettings) -> None:
    assert colour_settings(env) == expected


# --- make_console


def test_no_color_output_has_no_ansi_codes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NO_COLOR", "1")
    result = runner.invoke(app, ["--version"], color=False)
    assert not ANSI.search(result.output)
    buf = io.StringIO()
    make_console(file=buf).print("[success]✓ Pass[/success] [error]✕ Fail[/error] [accent]benchtop[/accent]")
    assert buf.getvalue() == "✓ Pass ✕ Fail benchtop\n"


@pytest.mark.parametrize("force", ["1", "0", ""])
def test_no_color_means_no_ansi_codes_even_when_forced(monkeypatch: pytest.MonkeyPatch, force: str) -> None:
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.setenv("FORCE_COLOR", force)
    monkeypatch.setenv("TERM", "xterm-256color")
    buf = io.StringIO()
    make_console(file=buf).print("[success]ok[/success] [error]bad[/error] [muted]note[/muted]")
    assert buf.getvalue() == "ok bad note\n"


@pytest.mark.parametrize("force", ["0", "false", "OFF"])
def test_force_color_zero_does_not_force_styling(monkeypatch: pytest.MonkeyPatch, force: str) -> None:
    # Regression: Rich alone treats FORCE_COLOR=0 as "force on", which leaked ANSI codes into pipes.
    monkeypatch.setenv("FORCE_COLOR", force)
    monkeypatch.setenv("TERM", "xterm-256color")
    buf = io.StringIO()
    make_console(file=buf).print("[error]bad[/error]")
    assert buf.getvalue() == "bad\n"


def test_explicit_env_overrides_the_process_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.setenv("TERM", "xterm-256color")
    buf = io.StringIO()
    make_console(file=buf, env={"FORCE_COLOR": "1"}).print("[error]x[/error]")
    assert ANSI.search(buf.getvalue())


def test_non_tty_output_is_plain_text() -> None:
    buf = io.StringIO()
    make_console(file=buf).print("[warning]▲ check[/warning]")
    assert buf.getvalue() == "▲ check\n"


def test_forced_colour_maps_semantic_styles_to_the_theme(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FORCE_COLOR", "1")
    monkeypatch.setenv("TERM", "xterm-256color")
    buf = io.StringIO()
    make_console(file=buf).print("[error]x[/error] [success]y[/success]")
    codes = ANSI.findall(buf.getvalue())
    assert "\x1b[1;31m" in codes  # error: bold red
    assert "\x1b[32m" in codes  # success: green


def test_theme_defines_the_semantic_styles() -> None:
    assert {"success", "warning", "error", "muted", "accent"} <= set(THEME.styles)
    assert set(STATUS_GLYPHS.values()) == {"✓", "▲", "✕", "•"}


def test_status_glyphs_are_read_only() -> None:
    with pytest.raises(TypeError):
        STATUS_GLYPHS["success"] = "ok"  # type: ignore[index]
