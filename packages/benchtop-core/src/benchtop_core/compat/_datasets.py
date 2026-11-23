# SPDX-FileCopyrightText: 2026 Benchtop Lab contributors
# SPDX-License-Identifier: Apache-2.0
"""Read-only access to LeRobot datasets (`codebase_version` v3.0): metadata, episodes, features and frames.

`open_dataset` returns a `DatasetView` made of plain dataclasses and NumPy arrays, so the dataset doctor and
the grader never touch LeRobot or PyTorch types. Nothing here can write to a dataset.
"""

import re
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final

import numpy as np
import numpy.typing as npt

from benchtop_core.compat._version import require_supported_lerobot
from benchtop_core.errors import BenchtopError

# LeRobot ships no type information, so its objects are `Any` inside this module and nowhere else.
__all__ = ["DatasetInfo", "DatasetView", "EpisodeInfo", "FeatureSpec", "Frame", "open_dataset"]

type Frame = dict[str, npt.NDArray[Any] | str]
"""One time step: feature name → array, plus the task instruction under `task`. Images are HWC `uint8`."""

_CAMERA_DTYPES: Final = frozenset({"image", "video"})
_REPO_ID: Final = re.compile(r"[\w.-]+/[\w.-]+")
_INFO_FILE: Final = Path("meta") / "info.json"


@dataclass(frozen=True, slots=True)
class FeatureSpec:
    """One column of a dataset.

    Attributes:
        dtype: `float32`, `int64`, `image`, `video`, ...
        shape: Shape of one value; camera features are `(height, width, channels)`.
        names: Component names for a flat list of names (e.g. the six joint names), otherwise `None`.
    """

    dtype: str
    shape: tuple[int, ...]
    names: tuple[str, ...] | None

    @property
    def is_camera(self) -> bool:
        """Whether the feature holds camera frames (stored as images or as video)."""
        return self.dtype in _CAMERA_DTYPES


@dataclass(frozen=True, slots=True)
class DatasetInfo:
    """Dataset-level metadata from `meta/info.json`.

    Attributes:
        codebase_version: The LeRobotDataset format version, e.g. `v3.0`.
        fps: Frames per second of the recording.
        robot_type: The robot that recorded the data, e.g. `so_follower`.
        total_episodes: Number of episodes.
        total_frames: Number of frames over all episodes.
        total_tasks: Number of distinct task instructions.
        splits: Split name → episode range, e.g. `{"train": "0:50"}`.
    """

    codebase_version: str
    fps: int
    robot_type: str | None
    total_episodes: int
    total_frames: int
    total_tasks: int
    splits: Mapping[str, str]


@dataclass(frozen=True, slots=True)
class EpisodeInfo:
    """One episode.

    Attributes:
        index: Episode index, starting at 0.
        length: Number of frames.
        tasks: The task instructions used in the episode.
        start: Dataset index of the episode's first frame.
        stop: Dataset index one past the episode's last frame.
    """

    index: int
    length: int
    tasks: tuple[str, ...]
    start: int
    stop: int


class DatasetView:
    """A read-only view of one LeRobot dataset.

    Metadata is loaded when the view is created; frames are read (and, for a Hub dataset, downloaded) only
    when asked for.

    Attributes:
        source: The folder or Hub repository id the view was opened from.
        root: The local dataset folder, or `None` for a Hub dataset in LeRobot's cache.
        info: Dataset-level metadata.
        features: Feature name → specification, in the dataset's column order.
        episodes: Every episode, in order.
        tasks: Task instructions, ordered by task index.
        stats: Feature name → statistic name (`mean`, `std`, `min`, `max`, `q01`, ...) → array.
    """

    def __init__(self, source: str, repo_id: str, root: Path | None, metadata: Any) -> None:  # noqa: ANN401
        self.source = source
        self.root = root
        self._repo_id = repo_id
        self._readers: dict[bool, Any] = {}
        raw = metadata.info
        self.info = DatasetInfo(
            codebase_version=str(raw.codebase_version),
            fps=int(raw.fps),
            robot_type=None if raw.robot_type is None else str(raw.robot_type),
            total_episodes=int(raw.total_episodes),
            total_frames=int(raw.total_frames),
            total_tasks=int(raw.total_tasks),
            splits=MappingProxyType({str(k): str(v) for k, v in (raw.splits or {}).items()}),
        )
        self.features: Mapping[str, FeatureSpec] = MappingProxyType(
            {str(name): _feature_spec(spec) for name, spec in metadata.features.items()}
        )
        self.tasks: tuple[str, ...] = _tasks(metadata.tasks)
        self.episodes: tuple[EpisodeInfo, ...] = _episodes(metadata.episodes)
        self.stats: Mapping[str, Mapping[str, npt.NDArray[Any]]] = MappingProxyType(
            {
                str(name): MappingProxyType({str(k): _read_only(np.asarray(v)) for k, v in values.items()})
                for name, values in (metadata.stats or {}).items()
            }
        )

    @property
    def camera_keys(self) -> tuple[str, ...]:
        """Names of the camera features, e.g. `observation.images.front`."""
        return tuple(name for name, spec in self.features.items() if spec.is_camera)

    def __len__(self) -> int:
        return self.info.total_frames

    def __repr__(self) -> str:
        return (
            f"DatasetView({self.source!r}, episodes={self.info.total_episodes}, "
            f"frames={self.info.total_frames}, fps={self.info.fps})"
        )

    def frame(self, index: int, *, images: bool = False) -> Frame:
        """Read one frame.

        Args:
            index: Dataset index in `range(len(view))`.
            images: Also decode the camera frames (slower). Images come back as HWC `uint8`.

        Returns:
            Feature name → NumPy array, and the task instruction under `task`.

        Raises:
            IndexError: If `index` is out of range.
        """
        if isinstance(index, bool) or not 0 <= index < len(self):
            raise IndexError(f"frame index {index} is out of range for a dataset of {len(self)} frames")
        reader = self._reader(images=images)
        item = reader[index] if images else reader.get_raw_item(index)
        frame: Frame = {}
        for key, value in item.items():
            if isinstance(value, str):
                frame[key] = value
                continue
            array = np.asarray(value)
            if key in self.features and self.features[key].is_camera:
                array = np.ascontiguousarray(np.moveaxis(array, 0, -1))  # LeRobot yields CHW; we use HWC
            frame[key] = array
        if "task" not in frame and "task_index" in frame:
            frame["task"] = self.tasks[int(np.asarray(frame["task_index"]).item())]
        return frame

    def episode_frames(self, episode: int, *, images: bool = False) -> Iterator[Frame]:
        """Iterate over the frames of one episode, in order.

        Args:
            episode: Episode index in `range(info.total_episodes)`.
            images: Also decode the camera frames (slower).

        Yields:
            Each frame, as returned by `frame`.

        Raises:
            IndexError: If `episode` is out of range.
        """
        if isinstance(episode, bool) or not 0 <= episode < len(self.episodes):
            raise IndexError(
                f"episode {episode} is out of range for a dataset of {len(self.episodes)} episodes"
            )
        info = self.episodes[episode]
        for index in range(info.start, info.stop):
            yield self.frame(index, images=images)

    def _reader(self, *, images: bool) -> Any:  # noqa: ANN401
        """Create (once) the LeRobot reader; without `images` a Hub dataset's videos are not downloaded."""
        if images not in self._readers:
            from lerobot.datasets import LeRobotDataset  # noqa: PLC0415  (lazy: imports torch)

            with _translated_errors(self.source):
                self._readers[images] = LeRobotDataset(
                    self._repo_id, root=self.root, download_videos=images, return_uint8=True
                )
        return self._readers[images]


def open_dataset(repo_or_path: str | Path, *, revision: str | None = None) -> DatasetView:
    """Open a LeRobot dataset read-only.

    Args:
        repo_or_path: A local dataset folder (the one containing `meta/info.json`), or a Hugging Face Hub
            dataset id such as `lerobot/pusht`. A Hub dataset's metadata is downloaded to LeRobot's cache.
        revision: Hub branch, tag or commit. Defaults to the dataset's `v3.0` tag.

    Returns:
        A read-only view of the dataset.

    Raises:
        BenchtopError: If the folder is not a LeRobot dataset, the Hub dataset cannot be fetched, the dataset
            uses an unsupported format version, or the installed LeRobot is outside the supported range.
    """
    require_supported_lerobot()
    source = str(repo_or_path)
    path = Path(repo_or_path).expanduser()
    if not source.strip():
        raise BenchtopError(
            "No dataset was given (the value is empty).",
            cause="an unset shell variable or a missing argument.",
            fix="pass a dataset folder or a Hub dataset id such as lerobot/pusht.",
        )
    if path.is_dir():
        if not (path / _INFO_FILE).is_file():
            raise BenchtopError(
                f"{source!r} is a folder, but not a LeRobot dataset: it has no {_INFO_FILE.as_posix()}.",
                cause="the path points at a parent folder or at an unfinished recording.",
                fix=f"pass the folder that contains meta/ and data/ (look with: ls {source}).",
            )
        repo_id, root = f"local/{path.resolve().name}", path
    elif isinstance(repo_or_path, str) and _REPO_ID.fullmatch(repo_or_path):
        repo_id, root = repo_or_path, None
    else:
        raise BenchtopError(
            f"No dataset found at {source!r}.",
            cause="the folder does not exist, and the value is not a Hub id of the form 'user/name'.",
            fix="check the path, or pass a Hub dataset id such as lerobot/pusht.",
        )

    from lerobot.datasets import LeRobotDatasetMetadata  # noqa: PLC0415  (lazy: imports torch)

    with _translated_errors(source):
        metadata = LeRobotDatasetMetadata(repo_id, root=root, revision=revision)
    return DatasetView(source, repo_id, root, metadata)


@contextmanager
def _translated_errors(source: str) -> Iterator[None]:
    """Turn LeRobot and Hub exceptions into a `BenchtopError` that says what to do next."""
    from lerobot.datasets.utils import CompatibilityError  # noqa: PLC0415  (lazy: imports torch)

    try:
        yield
    except BenchtopError:
        raise
    except CompatibilityError as exc:
        raise BenchtopError(
            f"The dataset {source!r} uses a format this LeRobot cannot read.",
            cause=f"it was recorded with a different LeRobotDataset version ({_first_line(exc)}).",
            fix="convert it with LeRobot's conversion script for v3.0, or re-record it with lerobot 0.7.",
        ) from exc
    except OSError as exc:
        raise BenchtopError(
            f"Could not read the dataset {source!r}.",
            cause=f"a file is missing or the Hugging Face Hub is unreachable ({_first_line(exc)}).",
            fix="check the dataset id and your connection, then run: benchtop doctor",
        ) from exc
    except Exception as exc:
        raise BenchtopError(
            f"Could not open the dataset {source!r}.",
            cause=f"its metadata is damaged or incomplete ({type(exc).__name__}: {_first_line(exc)}).",
            fix="re-download or re-record the dataset, then run: benchtop doctor",
        ) from exc


def _first_line(exc: BaseException) -> str:
    text = str(exc).strip()
    return text.splitlines()[0] if text else type(exc).__name__


def _read_only(array: npt.NDArray[Any]) -> npt.NDArray[Any]:
    array.setflags(write=False)
    return array


def _feature_spec(spec: Mapping[str, Any]) -> FeatureSpec:
    names = spec.get("names")
    flat = isinstance(names, list | tuple) and all(isinstance(name, str) for name in names)
    return FeatureSpec(
        dtype=str(spec["dtype"]),
        shape=tuple(int(size) for size in spec["shape"]),
        names=tuple(names) if flat and names is not None else None,
    )


def _tasks(table: Any) -> tuple[str, ...]:  # noqa: ANN401
    """Order the task instructions by task index (LeRobot stores a table indexed by instruction)."""
    if table is None:
        return ()
    pairs = zip(table["task_index"].tolist(), table.index.tolist(), strict=True)
    return tuple(str(task) for _, task in sorted(pairs))


def _episodes(table: Any) -> tuple[EpisodeInfo, ...]:  # noqa: ANN401
    if table is None:
        return ()
    columns = table.select_columns(
        ["episode_index", "length", "tasks", "dataset_from_index", "dataset_to_index"]
    ).to_dict()
    episodes = [
        EpisodeInfo(
            index=int(index),
            length=int(length),
            tasks=tuple(str(task) for task in tasks),
            start=int(start),
            stop=int(stop),
        )
        for index, length, tasks, start, stop in zip(
            columns["episode_index"],
            columns["length"],
            columns["tasks"],
            columns["dataset_from_index"],
            columns["dataset_to_index"],
            strict=True,
        )
    ]
    return tuple(sorted(episodes, key=lambda episode: episode.index))
