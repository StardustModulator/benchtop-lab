# SPDX-FileCopyrightText: 2026 Benchtop Lab contributors
# SPDX-License-Identifier: Apache-2.0
"""`open_dataset()` on a tiny LeRobot v3 dataset built in the test (no network)."""

import json
from collections.abc import Iterator
from importlib import metadata
from pathlib import Path

import numpy as np
import pytest

from benchtop_core import compat
from benchtop_core.errors import BenchtopError

JOINT_NAMES = tuple(
    f"{joint}.pos"
    for joint in ("shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper")
)
EPISODE_LENGTHS = (4, 6)
TASKS = ("reach the red cube", "reach the blue cube")
CAMERA = "observation.images.front"
SIDE = 64


def _state(episode: int, step: int) -> np.ndarray[tuple[int], np.dtype[np.float32]]:
    return np.full(6, 10 * episode + step, np.float32)


@pytest.fixture(scope="module")
def offline() -> Iterator[None]:
    """Fail loudly instead of touching the network: the unit suite must run offline."""
    with pytest.MonkeyPatch.context() as patch:
        patch.setenv("HF_HUB_OFFLINE", "1")
        yield


@pytest.fixture(scope="module")
def tiny_dataset(tmp_path_factory: pytest.TempPathFactory, offline: None) -> Path:
    """Two short SO-101-shaped episodes with one small camera, written with LeRobot's own writer.

    The camera is 64 by 64: LeRobot's AV1 encoder (SVT-AV1) kills the process with SIGFPE on 16 by 16 frames.
    """
    from lerobot.datasets import LeRobotDataset

    root = tmp_path_factory.mktemp("datasets") / "tiny"
    features = {
        "observation.state": {"dtype": "float32", "shape": (6,), "names": list(JOINT_NAMES)},
        "action": {"dtype": "float32", "shape": (6,), "names": list(JOINT_NAMES)},
        CAMERA: {"dtype": "video", "shape": (SIDE, SIDE, 3), "names": ["height", "width", "channels"]},
    }
    dataset = LeRobotDataset.create(
        "local/tiny", fps=30, features=features, root=root, robot_type="so_follower"
    )
    for episode, length in enumerate(EPISODE_LENGTHS):
        for step in range(length):
            dataset.add_frame(
                {
                    "observation.state": _state(episode, step),
                    "action": _state(episode, step) + 1,
                    CAMERA: np.full((SIDE, SIDE, 3), 200 if episode else 40, np.uint8),
                    "task": TASKS[episode],
                }
            )
        dataset.save_episode()
    dataset.finalize()
    return root


@pytest.fixture(scope="module")
def view(tiny_dataset: Path) -> compat.DatasetView:
    return compat.open_dataset(tiny_dataset)


def test_info(view: compat.DatasetView, tiny_dataset: Path) -> None:
    assert view.info == compat.DatasetInfo(
        codebase_version="v3.0",
        fps=30,
        robot_type="so_follower",
        total_episodes=2,
        total_frames=10,
        total_tasks=2,
        splits={"train": "0:2"},
    )
    assert len(view) == 10
    assert view.root == tiny_dataset
    assert view.source == str(tiny_dataset)
    assert "episodes=2" in repr(view)


def test_accepts_a_string_path(tiny_dataset: Path) -> None:
    assert compat.open_dataset(str(tiny_dataset)).info.total_frames == 10


def test_features(view: compat.DatasetView) -> None:
    assert view.features["observation.state"] == compat.FeatureSpec("float32", (6,), JOINT_NAMES)
    assert view.features["action"].names == JOINT_NAMES
    camera = view.features[CAMERA]
    assert (camera.dtype, camera.shape, camera.is_camera) == ("video", (SIDE, SIDE, 3), True)
    assert not view.features["action"].is_camera
    assert view.camera_keys == (CAMERA,)
    assert view.features["timestamp"].names is None
    assert {"timestamp", "frame_index", "episode_index", "index", "task_index"} <= set(view.features)


def test_episodes_and_tasks(view: compat.DatasetView) -> None:
    assert view.tasks == TASKS
    assert view.episodes == (
        compat.EpisodeInfo(index=0, length=4, tasks=(TASKS[0],), start=0, stop=4),
        compat.EpisodeInfo(index=1, length=6, tasks=(TASKS[1],), start=4, stop=10),
    )


def test_stats(view: compat.DatasetView) -> None:
    expected = np.mean([_state(e, s) + 1 for e, n in enumerate(EPISODE_LENGTHS) for s in range(n)], axis=0)
    assert np.allclose(view.stats["action"]["mean"], expected)
    assert {"mean", "std", "min", "max"} <= set(view.stats["action"])
    assert CAMERA in view.stats


def test_frame_without_images(view: compat.DatasetView) -> None:
    frame = view.frame(5)
    state = frame["observation.state"]
    assert isinstance(state, np.ndarray)
    assert state.dtype == np.float32
    assert np.array_equal(state, _state(1, 1))
    assert np.array_equal(frame["action"], _state(1, 1) + 1)
    assert int(np.asarray(frame["episode_index"])) == 1
    assert int(np.asarray(frame["frame_index"])) == 1
    assert frame["task"] == TASKS[1]
    assert CAMERA not in frame


def test_frame_with_images_is_hwc_uint8(view: compat.DatasetView) -> None:
    frame = view.frame(0, images=True)
    image = frame[CAMERA]
    assert isinstance(image, np.ndarray)
    assert image.shape == (SIDE, SIDE, 3)
    assert image.dtype == np.uint8
    assert abs(float(image.mean()) - 40) < 6  # lossy video codec
    assert abs(float(np.asarray(view.frame(9, images=True)[CAMERA]).mean()) - 200) < 6
    assert frame["task"] == TASKS[0]


def test_episode_frames(view: compat.DatasetView) -> None:
    frames = list(view.episode_frames(1))
    assert len(frames) == 6
    assert [int(np.asarray(frame["frame_index"])) for frame in frames] == list(range(6))
    assert all(frame["task"] == TASKS[1] for frame in frames)
    assert np.array_equal(frames[-1]["observation.state"], _state(1, 5))


@pytest.mark.parametrize("index", [-1, 10, 10_000, True])
def test_frame_index_out_of_range(view: compat.DatasetView, index: int) -> None:
    with pytest.raises(IndexError, match="out of range"):
        view.frame(index)


@pytest.mark.parametrize("episode", [-1, 2, True])
def test_episode_out_of_range(view: compat.DatasetView, episode: int) -> None:
    with pytest.raises(IndexError, match="out of range"):
        next(view.episode_frames(episode))


def test_the_view_is_read_only(view: compat.DatasetView, tiny_dataset: Path) -> None:
    before = {path: path.stat().st_mtime_ns for path in tiny_dataset.rglob("*") if path.is_file()}
    with pytest.raises(TypeError):
        view.features["extra"] = view.features["action"]  # type: ignore[index]
    with pytest.raises(TypeError):
        view.stats["action"]["mean"] = np.zeros(6)  # type: ignore[index]
    with pytest.raises(ValueError, match="read-only"):
        view.stats["action"]["mean"][0] = 1.0
    with pytest.raises(AttributeError):
        view.info.fps = 60  # type: ignore[misc]
    assert not {
        name for name in dir(view) if name.startswith(("add_", "save_", "push_", "write", "finalize"))
    }
    view.frame(3, images=True)
    after = {path: path.stat().st_mtime_ns for path in tiny_dataset.rglob("*") if path.is_file()}
    assert after == before


def test_a_folder_that_is_not_a_dataset(tmp_path: Path, offline: None) -> None:
    (tmp_path / "data").mkdir()
    with pytest.raises(BenchtopError, match="not a LeRobot dataset") as caught:
        compat.open_dataset(tmp_path)
    assert "meta/info.json" in caught.value.what


@pytest.mark.parametrize("value", ["", "   "])
def test_an_empty_value_is_not_the_current_folder(value: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(Path(__file__).parent)
    with pytest.raises(BenchtopError, match="No dataset was given"):
        compat.open_dataset(value)


@pytest.mark.parametrize("value", ["./does/not/exist", "nope", "a/b/c"])
def test_a_path_that_does_not_exist(value: str, offline: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(Path(__file__).parent)
    with pytest.raises(BenchtopError, match="No dataset found") as caught:
        compat.open_dataset(value)
    assert "lerobot/pusht" in caught.value.fix


def test_a_hub_id_that_cannot_be_fetched(
    offline: None, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HF_LEROBOT_HOME", str(tmp_path))
    with pytest.raises(BenchtopError, match="Could not read the dataset 'benchtop-lab/missing'") as caught:
        compat.open_dataset("benchtop-lab/missing")
    assert "benchtop doctor" in caught.value.fix


def test_a_dataset_from_another_format_version(tiny_dataset: Path, tmp_path: Path, offline: None) -> None:
    old = tmp_path / "old"
    (old / "meta").mkdir(parents=True)
    info = json.loads((tiny_dataset / "meta" / "info.json").read_text(encoding="utf-8"))
    info["codebase_version"] = "v2.1"
    (old / "meta" / "info.json").write_text(json.dumps(info), encoding="utf-8")
    (old / "meta" / "stats.json").write_text(
        (tiny_dataset / "meta" / "stats.json").read_text(), encoding="utf-8"
    )
    with pytest.raises(BenchtopError, match="format this LeRobot cannot read") as caught:
        compat.open_dataset(old)
    assert "convert" in caught.value.fix


def test_damaged_metadata(tmp_path: Path, offline: None) -> None:
    (tmp_path / "meta").mkdir()
    (tmp_path / "meta" / "info.json").write_text("{not json", encoding="utf-8")
    with pytest.raises(BenchtopError, match="Could not open the dataset") as caught:
        compat.open_dataset(tmp_path)
    assert "damaged" in caught.value.cause


def test_an_unsupported_lerobot_is_refused_before_reading(
    tiny_dataset: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real_version = metadata.version
    monkeypatch.setattr(
        metadata, "version", lambda name: "0.8.0" if name == "lerobot" else real_version(name)
    )
    with pytest.raises(BenchtopError, match=r"LeRobot 0\.8\.0"):
        compat.open_dataset(tiny_dataset)


@pytest.mark.network
def test_opens_pusht_metadata_from_the_hub(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HF_LEROBOT_HOME", str(tmp_path))
    monkeypatch.delenv("HF_HUB_OFFLINE", raising=False)
    view = compat.open_dataset("lerobot/pusht")
    assert view.root is None
    assert view.info.codebase_version == "v3.0"
    assert view.info.total_episodes == len(view.episodes) > 100
    assert view.info.total_frames == view.episodes[-1].stop
    assert {"observation.state", "action"} <= set(view.features)
    assert view.tasks
