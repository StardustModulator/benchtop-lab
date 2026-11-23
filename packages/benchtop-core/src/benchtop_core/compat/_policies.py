# SPDX-FileCopyrightText: 2026 Benchtop Lab contributors
# SPDX-License-Identifier: Apache-2.0
"""Loading pretrained LeRobot policies: the surface is fixed here, the implementation arrives in S26."""

from pathlib import Path
from typing import Protocol, runtime_checkable

import numpy as np
import numpy.typing as npt

from benchtop_core.errors import BenchtopError

__all__ = ["LoadedPolicy", "load_policy"]


@runtime_checkable
class LoadedPolicy(Protocol):
    """A pretrained policy with its pre- and post-processors, reduced to plain NumPy in and out.

    Attributes:
        device: The device the policy runs on (`cpu`, `cuda` or `mps`).
    """

    device: str

    def reset(self) -> None:
        """Clear per-episode state (action queues, temporal ensembles) before a new episode."""

    def act(self, observation: dict[str, npt.NDArray[np.generic]]) -> npt.NDArray[np.float32]:
        """Return the next action for one environment observation.

        Args:
            observation: The environment observation (`pixels`, `agent_pos`, optional `environment_state`).

        Returns:
            One absolute joint-position action, `float32[6]` for the SO-101.
        """


def load_policy(path: str | Path, device: str = "cpu") -> LoadedPolicy:
    """Load a pretrained LeRobot policy and its processors.

    Not implemented yet: this stub fixes the signature other packages program against. The LeRobot checkpoint
    adapter (session S26) implements it, including `PolicyOutput` handling.

    Args:
        path: A checkpoint's `pretrained_model/` folder or a Hub repository id.
        device: `cpu`, `cuda` or `mps`.

    Raises:
        BenchtopError: Always, until the checkpoint adapter lands.
    """
    raise BenchtopError(
        f"Loading LeRobot policies is not available yet (asked for {str(path)!r} on {device!r}).",
        cause="the LeRobot checkpoint adapter is planned for a later Benchtop Lab release.",
        fix="evaluate the checkpoint with LeRobot's own `lerobot-eval` for now.",
    )
