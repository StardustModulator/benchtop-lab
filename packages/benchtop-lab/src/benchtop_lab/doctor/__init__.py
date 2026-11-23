# SPDX-FileCopyrightText: 2026 Benchtop Lab contributors
# SPDX-License-Identifier: Apache-2.0
"""`benchtop doctor`: check that this machine can run Benchtop Lab, and say how to fix what cannot."""

from benchtop_lab.doctor.checks import CheckResult, DoctorReport, Probes, Status, run_checks
from benchtop_lab.doctor.report import print_report

__all__ = ["CheckResult", "DoctorReport", "Probes", "Status", "print_report", "run_checks"]
