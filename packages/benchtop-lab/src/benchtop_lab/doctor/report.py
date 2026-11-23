# SPDX-FileCopyrightText: 2026 Benchtop Lab contributors
# SPDX-License-Identifier: Apache-2.0
"""Human-readable output of `benchtop doctor`: a status table, the fixes, and a one-line verdict.

Status is never colour-only (ui-excellence skill): every row carries a glyph and a word, so the output reads the
same with `NO_COLOR`, in a pipe and on light or dark terminals.
"""

from collections.abc import Mapping
from types import MappingProxyType
from typing import Final

from rich import box
from rich.console import Console
from rich.markup import escape
from rich.table import Table
from rich.text import Text

from benchtop_lab.console import STATUS_GLYPHS
from benchtop_lab.doctor.checks import DoctorReport, Status

__all__ = ["print_report", "verdict"]

_STYLE: Final[Mapping[Status, tuple[str, str]]] = MappingProxyType(
    {
        Status.PASS: ("success", STATUS_GLYPHS["success"]),
        Status.WARN: ("warning", STATUS_GLYPHS["warning"]),
        Status.FAIL: ("error", STATUS_GLYPHS["error"]),
        Status.SKIP: ("muted", STATUS_GLYPHS["info"]),
    }
)


def _label(status: Status) -> Text:
    style, glyph = _STYLE[status]
    return Text(f"{glyph} {status.value}", style=style)


def _plural(count: int, word: str) -> str:
    return f"{count} {word}" if count == 1 else f"{count} {word}s"


def verdict(report: DoctorReport) -> str:
    """Summarise a report in one plain sentence.

    Args:
        report: The report to summarise.

    Returns:
        `Ready ...` with the counts, or `Not ready ...` with the number of required checks that failed.
    """
    if not report.ok:
        failed = sum(result.required and result.status is Status.FAIL for result in report.results)
        return f"Not ready: {_plural(failed, 'required check')} failed. Apply the fixes above, then run: benchtop doctor"
    parts = [f"{report.count(Status.PASS)} passed"]
    if report.count(Status.WARN):
        parts.append(_plural(report.count(Status.WARN), "warning"))
    if report.count(Status.FAIL):
        parts.append(f"{report.count(Status.FAIL)} optional failed")
    if report.count(Status.SKIP):
        parts.append(f"{report.count(Status.SKIP)} skipped")
    return f"Ready: {', '.join(parts)}."


def print_report(report: DoctorReport, console: Console) -> None:
    """Print the report as a table, followed by the fixes and the verdict.

    Args:
        report: The report from `run_checks`.
        console: The console to print to (use `benchtop_lab.console.make_console`).
    """
    table = Table(box=box.SIMPLE_HEAD, pad_edge=False, header_style="accent", expand=False)
    table.add_column("Status", no_wrap=True)
    table.add_column("Check", no_wrap=True)
    table.add_column("Result", overflow="fold")
    for result in report.results:
        table.add_row(_label(result.status), result.title, Text(result.summary))

    console.print()
    console.print("[accent]Benchtop Lab doctor[/accent]")
    console.print(table)

    to_fix = [r for r in report.results if r.fix and r.status in {Status.FAIL, Status.WARN}]
    if to_fix:
        console.print("[accent]How to fix[/accent]")
        for result in to_fix:
            style, glyph = _STYLE[result.status]
            need = "required" if result.required and result.status is Status.FAIL else "recommended"
            console.print(f"  [{style}]{glyph}[/{style}] {escape(result.title)} [muted]({need})[/muted]")
            console.print(Text(f"    {result.fix}"), soft_wrap=True)
        console.print()

    style, glyph = _STYLE[Status.PASS if report.ok else Status.FAIL]
    console.print(f"[{style}]{glyph} {escape(verdict(report))}[/{style}]", soft_wrap=True)
