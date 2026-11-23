# SPDX-FileCopyrightText: 2026 Benchtop Lab contributors
# SPDX-License-Identifier: Apache-2.0
"""Errors shown to users: what happened, the likely cause, and the next command to run (ARCHITECTURE §8)."""

__all__ = ["BenchtopError"]


class BenchtopError(Exception):
    """An error a learner can act on.

    Attributes:
        what: What happened, in one sentence.
        cause: The most likely cause.
        fix: The next command to run or step to take.
    """

    def __init__(self, what: str, *, cause: str, fix: str) -> None:
        super().__init__(f"{what} Likely cause: {cause} Next step: {fix}")
        self.what = what
        self.cause = cause
        self.fix = fix
