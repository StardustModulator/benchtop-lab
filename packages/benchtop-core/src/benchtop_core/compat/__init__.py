# SPDX-FileCopyrightText: 2026 Benchtop Lab contributors
# SPDX-License-Identifier: Apache-2.0
"""The LeRobot boundary: with `benchtop_core.policies` (ADR-007), the only module that imports LeRobot.

Everything else in the monorepo uses the typed wrappers exported here, so a LeRobot API change is fixed in one
place and caught by the contract tests in `packages/benchtop-core/tests/compat/`.

Importing this package is cheap: `lerobot` and `torch` are imported only when a function that needs them is
called (PLAN §11), so `benchtop --help` and sim-only commands start fast.
"""

from benchtop_core.compat._datasets import (
    DatasetInfo,
    DatasetView,
    EpisodeInfo,
    FeatureSpec,
    Frame,
    open_dataset,
)
from benchtop_core.compat._policies import LoadedPolicy, load_policy
from benchtop_core.compat._runtime import HubLogin, TorchInfo, hub_login, torch_info
from benchtop_core.compat._version import (
    SUPPORTED_LEROBOT,
    LeRobotVersion,
    lerobot_version,
    require_supported_lerobot,
)

__all__ = [
    "SUPPORTED_LEROBOT",
    "DatasetInfo",
    "DatasetView",
    "EpisodeInfo",
    "FeatureSpec",
    "Frame",
    "HubLogin",
    "LeRobotVersion",
    "LoadedPolicy",
    "TorchInfo",
    "hub_login",
    "lerobot_version",
    "load_policy",
    "open_dataset",
    "require_supported_lerobot",
    "torch_info",
]
