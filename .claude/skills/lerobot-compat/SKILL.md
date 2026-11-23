---
name: lerobot-compat
description: How Benchtop Lab talks to LeRobot 0.7.x. Use when writing or changing benchtop_core.compat, policy adapters, dataset writers/readers, EnvHub exports, or anything that calls lerobot or its CLI commands.
---

# LeRobot compatibility (pinned: lerobot 0.7.x, Python 3.12+)

## Rules
- Only `benchtop_core.compat` (and the `benchtop_core.policies` plugin, ADR-007) import `lerobot`. Everything else uses compat's typed wrappers.
- Verify APIs against the installed package, not memory: `uv run python -c "import lerobot, inspect; ..."` and read
  the source under `.venv/lib/python3.12/site-packages/lerobot/`. LeRobot changes APIs every minor release.
- Add a contract test for every LeRobot behaviour we rely on (`packages/benchtop-core/tests/compat/`).

## Facts for 0.7 (verified against the installed 0.7.0 in S03, 23 Nov 2026; re-verify when upgrading)
Each fact has a contract test in `packages/benchtop-core/tests/compat/test_lerobot_contract.py`.
- Simulators live in `lerobot.sim.integrations.<sim>`; env configs are named `*EnvConfig`; `--env.type` unchanged.
- Envs return canonical observations: HWC uint8 images, flat float32 state. Map camera names with `--rename_map`.
- EnvHub: a folder or Space with `env.py` defining `make_env(n_envs=1, use_async_envs=False, **kwargs)` returning
  `{suite: {task_id: vector_env}}` built from per-env factories, unwrapped `SyncVectorEnv`/`AsyncVectorEnv`.
  Local folder: `--env.type=envhub --env.hub_path=./envhub/<task> --env.trust_remote_code=true`; options for
  `make_env` go in `--env.make_env_kwargs`. `LEROBOT_SIM` accepts exactly `fps, control_mode, semantics,
  state_names, action_names, robot_type`; an unknown key raises.
- Env contract: obs dict with `pixels` (image or dict of images), `agent_pos`, optional `environment_state`;
  1-D continuous `Box` action; `task_description`; `_max_episode_steps`; `info["is_success"]` every step;
  optional `info["metrics"]` (`{name: float}`) kept per episode by `lerobot-eval`.
- Sim robot: `--robot.type=sim --robot.env.type=envhub --robot.env.hub_path=...` works with `lerobot-record`,
  `lerobot-teleoperate`, `lerobot-rollout`, `lerobot-replay`. `--teleop.type=so101_leader` drives an SO-101 twin when
  the env declares the follower's action names/units via `LEROBOT_SIM`.
- `lerobot-eval` reports success with a 95% Wilson interval (`pc_success_ci95`, in percent), from
  `lerobot.utils.eval_stats.wilson_interval` (no continuity correction; `nan` bounds for 0 trials; the lower bound
  at 0 successes is ~3e-17, not exactly 0, so compare with a tolerance).
- `select_action` / `predict_action_chunk` may return a `PolicyOutput` (`{"action", "prediction"}`); use
  `policy_output_to_transition` (`lerobot.processor.converters`) when calling directly. `PolicyOutput` lives in
  `lerobot.lerobot_types`; its runtime `__required_keys__` wrongly lists `prediction` (postponed annotations).
- `dtype` is the parameter-precision key in policy configs; pass `torch.bfloat16`/`torch.float16` objects in
  Python (a string raises). `use_amp` still exists as a separate mixed-precision switch.
- W&B was replaced by Trackio (`--trackio.*`). Remote inference: `lerobot[remote]`, `lerobot-policy-server`.
- Datasets: LeRobotDataset `codebase_version` v3.0; `add_frame(frame)` needs a `task` per frame; call `finalize()`.
  They need the `lerobot[dataset]` extra (datasets, pandas, pyarrow, av, torchcodec). A dataset opened with
  `LeRobotDataset(repo_id, root=...)` is read-only; items are CHW tensors (`return_uint8=True` keeps uint8).
  An existing local folder without `meta/info.json` makes LeRobot fall back to the Hub: check the folder first.
- LeRobot and MuJoCo ship no `py.typed`; mypy treats them as untyped (override in the root `pyproject.toml`).
- SO-101 device types are `so101_follower` (robot) and `so101_leader` (teleoperator).
- Install on Linux pulls CUDA 13 torch from PyPI; for CPU-only CI use the PyTorch CPU index (`--extra cpu`),
  and take torchvision from the same index. LeRobot requires `torch>=2.7,<2.16`.
- `import lerobot` and `lerobot.utils.eval_stats` are cheap and do not import torch; `lerobot.datasets`,
  `lerobot.envs` and the policies do (1–3 s).

## Headless
- `MUJOCO_GL=egl` (fallback `osmesa`). Create renderers on first `reset()`, not in `__init__`.
