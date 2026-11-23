# SPDX-FileCopyrightText: 2026 Benchtop Lab contributors
# SPDX-License-Identifier: Apache-2.0
"""Contract tests: one test per LeRobot 0.7 fact Benchtop Lab relies on (lerobot-compat skill, PLAN §2).

These run against the installed LeRobot. When one fails after an upgrade, LeRobot changed something we depend
on: fix `benchtop_core.compat` (and the skill), not the test.
"""

import dataclasses
import importlib
import math
import textwrap
from importlib import metadata
from pathlib import Path
from typing import Any

import numpy as np
import pytest

JOINTS = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]
JOINT_NAMES = [f"{joint}.pos" for joint in JOINTS]

ENV_PY = textwrap.dedent(
    """
    import gymnasium as gym
    import numpy as np

    JOINTS = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]
    JOINT_NAMES = [f"{joint}.pos" for joint in JOINTS]
    LEROBOT_SIM = {
        "fps": 30,
        "control_mode": "position",
        "semantics": "so101-joint-degrees-v1",
        "state_names": JOINT_NAMES,
        "action_names": JOINT_NAMES,
        "robot_type": "so_follower",
    }


    class ToyEnv(gym.Env):
        metadata = {"render_modes": ["rgb_array"], "render_fps": 30}

        def __init__(self, succeed_at=2, **options):
            self.options = options
            self.succeed_at = succeed_at
            self.task_description = "Move the arm to the target."
            self._max_episode_steps = 5
            self.observation_space = gym.spaces.Dict(
                {
                    "pixels": gym.spaces.Dict(
                        {"front": gym.spaces.Box(0, 255, (8, 8, 3), np.uint8)}
                    ),
                    "agent_pos": gym.spaces.Box(-180, 180, (6,), np.float32),
                    "environment_state": gym.spaces.Box(-1, 1, (3,), np.float32),
                }
            )
            self.action_space = gym.spaces.Box(-180, 180, (6,), np.float32)
            self._t = 0

        def _obs(self):
            return {
                "pixels": {"front": np.full((8, 8, 3), self._t, np.uint8)},
                "agent_pos": np.full(6, self._t, np.float32),
                "environment_state": np.zeros(3, np.float32),
            }

        def reset(self, *, seed=None, options=None):
            super().reset(seed=seed)
            self._t = 0
            return self._obs(), {"is_success": False}

        def step(self, action):
            self._t += 1
            success = self._t >= self.succeed_at
            info = {"is_success": success, "metrics": {"progress": self._t / self.succeed_at}}
            return self._obs(), float(success), success, self._t >= self._max_episode_steps, info


    def make_env(n_envs=1, use_async_envs=False, **kwargs):
        vector = gym.vector.AsyncVectorEnv if use_async_envs else gym.vector.SyncVectorEnv
        return {"toy": {0: vector([lambda: ToyEnv(**kwargs) for _ in range(n_envs)])}}
    """
)


@pytest.fixture
def hub_folder(tmp_path: Path) -> Path:
    """A local EnvHub folder with a toy SO-101-shaped environment."""
    folder = tmp_path / "toy-envhub"
    folder.mkdir()
    (folder / "env.py").write_text(ENV_PY, encoding="utf-8")
    return folder


def test_lerobot_is_the_pinned_minor_and_apache_licensed() -> None:
    assert metadata.version("lerobot").startswith("0.7.")
    assert metadata.metadata("lerobot")["License"] == "Apache-2.0" or "Apache" in str(
        metadata.metadata("lerobot").get("License-Expression", "")
    )


@pytest.mark.parametrize(
    ("module", "names"),
    [
        ("lerobot.sim", ["LocalVectorEnv", "SimConfig", "StepResult"]),
        ("lerobot.sim.integrations.envhub", ["make_envs", "env_fns", "conventions", "SIM_DEFAULTS"]),
        ("lerobot.sim.integrations.utils", ["canonical_observation"]),
        ("lerobot.envs.configs", ["EnvConfig", "HubEnvConfig"]),
        ("lerobot.envs.factory", ["make_env", "make_env_config"]),
        ("lerobot.datasets", ["LeRobotDataset", "LeRobotDatasetMetadata", "CODEBASE_VERSION"]),
        ("lerobot.datasets.utils", ["CompatibilityError"]),
        ("lerobot.utils.eval_stats", ["wilson_interval", "success_summary"]),
        ("lerobot.lerobot_types", ["PolicyOutput"]),
        ("lerobot.processor.converters", ["policy_output_to_transition"]),
        ("lerobot.policies.pretrained", ["PreTrainedPolicy"]),
        ("lerobot.configs.policies", ["PreTrainedConfig"]),
        ("lerobot.configs.default", ["TrackioConfig"]),
        ("lerobot.robots.sim_robot.config_sim_robot", ["SimRobotConfig"]),
    ],
)
def test_module_paths(module: str, names: list[str]) -> None:
    loaded = importlib.import_module(module)
    missing = [name for name in names if not hasattr(loaded, name)]
    assert not missing, f"{module} no longer provides {missing}"


def test_command_line_tools_exist() -> None:
    scripts = {entry.name for entry in metadata.entry_points(group="console_scripts")}
    expected = {
        "lerobot-eval",
        "lerobot-train",
        "lerobot-record",
        "lerobot-teleoperate",
        "lerobot-rollout",
        "lerobot-replay",
        "lerobot-policy-server",
    }
    assert expected <= scripts


def test_env_configs_are_named_envconfig_and_envhub_is_registered() -> None:
    from lerobot.envs.configs import EnvConfig, HubEnvConfig

    choices = EnvConfig.get_known_choices()
    assert choices["envhub"] is HubEnvConfig
    assert all(cls.__name__.endswith("EnvConfig") for cls in choices.values())


def test_envhub_loader_flags() -> None:
    from lerobot.envs.configs import HubEnvConfig

    fields = {field.name: field.default for field in dataclasses.fields(HubEnvConfig)}
    assert {"hub_path", "trust_remote_code", "make_env_kwargs", "use_native_batch"} <= set(fields)
    assert fields["trust_remote_code"] is False


def test_envhub_refuses_to_run_code_without_trust(hub_folder: Path) -> None:
    from lerobot.sim.integrations.envhub import make_envs

    with pytest.raises(RuntimeError, match="trust_remote_code"):
        make_envs(str(hub_folder), n_envs=1, use_async_envs=False)


def test_envhub_make_env_signature_and_return_shape(hub_folder: Path) -> None:
    import gymnasium as gym
    from lerobot.sim.integrations.envhub import env_fns, make_envs

    envs = make_envs(str(hub_folder), n_envs=2, use_async_envs=False, trust_remote_code=True, succeed_at=3)
    try:
        vector = envs["toy"][0]
        assert type(vector) is gym.vector.SyncVectorEnv
        assert vector.num_envs == 2
        assert getattr(vector.envs[0].unwrapped, "succeed_at") == 3  # noqa: B009  (**kwargs reach make_env)
    finally:
        for vector in envs["toy"].values():
            vector.close()

    factories = env_fns("unused", 2, str(hub_folder), trust_remote_code=True)
    assert len(factories["toy"][0]) == 2
    env = factories["toy"][0][0]()
    assert env.task_description == "Move the arm to the target."
    env.close()


def test_envhub_lerobot_sim_conventions(hub_folder: Path) -> None:
    from lerobot.sim.integrations.envhub import SIM_DEFAULTS, conventions

    assert set(SIM_DEFAULTS) == {
        "fps",
        "control_mode",
        "semantics",
        "state_names",
        "action_names",
        "robot_type",
    }
    declared = conventions({"hub_path": str(hub_folder), "trust_remote_code": True})
    assert declared == {
        "fps": 30,
        "control_mode": "position",
        "semantics": "so101-joint-degrees-v1",
        "state_names": JOINT_NAMES,
        "action_names": JOINT_NAMES,
        "robot_type": "so_follower",
    }


def test_envhub_rejects_unknown_lerobot_sim_keys(tmp_path: Path) -> None:
    from lerobot.sim.integrations.envhub import conventions

    folder = tmp_path / "bad-envhub"
    folder.mkdir()
    (folder / "env.py").write_text(ENV_PY.replace('"fps": 30', '"fpz": 30'), encoding="utf-8")
    with pytest.raises(ValueError, match="fpz"):
        conventions({"hub_path": str(folder), "trust_remote_code": True})


def test_canonical_observation_keys_and_types() -> None:
    from lerobot.sim.integrations.utils import canonical_observation

    obs = {
        "pixels": {"front": np.zeros((8, 8, 3), np.uint8), "wrist": np.ones((8, 8, 3), np.uint8)},
        "agent_pos": np.arange(6, dtype=np.float64),
        "environment_state": np.zeros(3, np.float64),
    }
    canonical = canonical_observation(obs)
    assert set(canonical) == {
        "observation.images.front",
        "observation.images.wrist",
        "observation.state",
        "observation.environment_state",
    }
    assert canonical["observation.images.front"].dtype == np.uint8
    assert canonical["observation.images.front"].shape == (8, 8, 3)
    assert canonical["observation.state"].dtype == np.float32
    assert canonical["observation.environment_state"].dtype == np.float32


@pytest.mark.parametrize(
    "image",
    [np.zeros((3, 8, 8), np.uint8), np.zeros((8, 8, 3), np.float32), np.zeros((8, 8), np.uint8)],
    ids=["chw", "float", "greyscale"],
)
def test_canonical_observation_rejects_images_that_are_not_hwc_uint8(image: np.ndarray[Any, Any]) -> None:
    from lerobot.sim.integrations.utils import canonical_observation

    with pytest.raises(ValueError, match="HWC uint8"):
        canonical_observation({"pixels": {"front": image}})


def test_env_contract_through_make_env(hub_folder: Path) -> None:
    """`is_success` every step, `metrics`, `task_description`, `_max_episode_steps`, 1-D Box action."""
    import gymnasium as gym
    from lerobot.envs.configs import HubEnvConfig
    from lerobot.envs.factory import make_env

    config = HubEnvConfig(hub_path=str(hub_folder), trust_remote_code=True, make_env_kwargs={"succeed_at": 2})
    envs = make_env(config, n_envs=2)
    vector = envs["toy"][0]
    try:
        obs, info = vector.reset(seed=[0, 1])
        assert obs["observation.images.front"].shape == (2, 8, 8, 3)
        assert obs["observation.images.front"].dtype == np.uint8
        assert obs["observation.state"].shape == (2, 6)
        assert obs["observation.state"].dtype == np.float32
        assert obs["observation.environment_state"].shape == (2, 3)
        assert list(info["is_success"]) == [False, False]

        assert isinstance(vector.single_action_space, gym.spaces.Box)
        assert vector.single_action_space.shape == (6,)
        assert vector.call("task_description") == ("Move the arm to the target.",) * 2
        assert vector.call("_max_episode_steps") == (5, 5)

        action = np.zeros((2, 6), np.float32)
        _, _, terminated, _, info = vector.step(action)
        assert list(info["is_success"]) == [False, False]
        assert not terminated.any()
        _, reward, terminated, _, info = vector.step(action)
        assert list(info["is_success"]) == [True, True]
        assert terminated.all()
        assert list(reward) == [1.0, 1.0]
        assert np.allclose(info["metrics"]["progress"], 1.0)
    finally:
        vector.close()


def test_sim_robot_and_so101_devices_are_registered() -> None:
    from lerobot.robots.config import RobotConfig
    from lerobot.robots.sim_robot.config_sim_robot import SimRobotConfig
    from lerobot.teleoperators.config import TeleoperatorConfig

    importlib.import_module("lerobot.robots.so_follower.config_so_follower")
    importlib.import_module("lerobot.teleoperators.so_leader.config_so_leader")
    assert RobotConfig.get_known_choices()["sim"] is SimRobotConfig
    assert "so101_follower" in RobotConfig.get_known_choices()
    assert "so101_leader" in TeleoperatorConfig.get_known_choices()
    assert {"env", "task_id"} <= {field.name for field in dataclasses.fields(SimRobotConfig)}


def test_wilson_interval_helper() -> None:
    from lerobot.utils.eval_stats import success_summary, wilson_interval

    low, high = wilson_interval(9, 10)
    assert low == pytest.approx(0.59585, abs=1e-5)
    assert high == pytest.approx(0.98212, abs=1e-5)
    # Floating-point residue: the bound at 0 successes is about 3e-17, not exactly 0. Use a tolerance.
    assert wilson_interval(0, 10)[0] == pytest.approx(0.0, abs=1e-12)
    assert wilson_interval(10, 10)[1] == pytest.approx(1.0, abs=1e-12)
    assert all(math.isnan(bound) for bound in wilson_interval(0, 0))
    with pytest.raises(ValueError, match="impossible counts"):
        wilson_interval(11, 10)

    summary = success_summary([True, True, False, True])
    assert set(summary) == {"n_episodes", "n_success", "pc_success", "pc_success_ci95"}
    assert summary["pc_success"] == 75.0
    assert summary["pc_success_ci95"] == pytest.approx([100 * b for b in wilson_interval(3, 4)])


def test_policy_output_and_its_converter() -> None:
    import torch
    from lerobot.lerobot_types import PolicyOutput
    from lerobot.processor.converters import policy_output_to_transition

    # `prediction` is NotRequired for type checkers, but the module uses postponed annotations, so the runtime
    # `__required_keys__` lists both keys. Only the key names are a dependable runtime fact.
    assert set(PolicyOutput.__annotations__) == {"action", "prediction"}

    action = torch.arange(6, dtype=torch.float32).unsqueeze(0)
    for output in (action, {"action": action}):
        transition = policy_output_to_transition(output)
        assert torch.equal(transition["action"], action)
    assert {"observation", "action", "prediction", "reward", "done", "truncated", "info"} <= {
        str(getattr(key, "value", key)) for key in transition
    }


def test_policy_config_dtype_takes_torch_dtype_objects_and_use_amp_still_exists() -> None:
    """`dtype` sets the parameter precision and takes `torch.dtype` objects; `use_amp` is a separate flag."""
    import torch
    from lerobot.configs.policies import PreTrainedConfig
    from lerobot.policies.act.configuration_act import ACTConfig

    fields = {field.name: field.default for field in dataclasses.fields(PreTrainedConfig)}
    assert fields["dtype"] is None
    assert fields["use_amp"] is False
    assert not {"precision", "torch_dtype"} & set(fields)

    assert ACTConfig(device="cpu", dtype=torch.float16).dtype is torch.float16
    with pytest.raises(ValueError, match=r"torch\.dtype"):
        ACTConfig(device="cpu", dtype="float16")


def test_experiment_tracking_is_trackio_not_wandb() -> None:
    from lerobot.configs.train import TrainPipelineConfig

    fields = {field.name for field in dataclasses.fields(TrainPipelineConfig)}
    assert "trackio" in fields
    assert "wandb" not in fields


def test_dataset_v3_writer(tmp_path: Path) -> None:
    """`codebase_version` v3.0; `add_frame` needs a `task`; `finalize()`; reopened datasets are read-only."""
    from lerobot.datasets import CODEBASE_VERSION, LeRobotDataset

    assert CODEBASE_VERSION == "v3.0"
    features = {
        "observation.state": {"dtype": "float32", "shape": (6,), "names": JOINT_NAMES},
        "action": {"dtype": "float32", "shape": (6,), "names": JOINT_NAMES},
    }
    root = tmp_path / "dataset"
    dataset = LeRobotDataset.create(
        "local/contract", fps=30, features=features, root=root, robot_type="so_follower"
    )
    frame = {"observation.state": np.zeros(6, np.float32), "action": np.ones(6, np.float32)}
    with pytest.raises(ValueError, match="task"):
        dataset.add_frame(dict(frame))
    dataset.clear_episode_buffer()
    for _ in range(3):
        dataset.add_frame({**frame, "task": "reach"})
    dataset.save_episode()
    dataset.finalize()
    dataset.finalize()  # idempotent

    assert (root / "meta" / "info.json").is_file()
    assert (root / "meta" / "tasks.parquet").is_file()
    assert (root / "data" / "chunk-000" / "file-000.parquet").is_file()

    reopened = LeRobotDataset("local/contract", root=root)
    assert reopened.meta.info.codebase_version == "v3.0"
    assert (reopened.num_episodes, reopened.num_frames, reopened.fps) == (1, 3, 30)
    assert reopened[0]["task"] == "reach"
    with pytest.raises(RuntimeError, match="read-only"):
        reopened.add_frame({**frame, "task": "reach"})
