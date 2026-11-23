---
title: Install from source
description: Clone the repository, create the environment with uv, and run the benchtop command.
---

<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Install from source

Until the first release, Benchtop Lab is installed from a clone of the repository. This takes a few minutes and
needs no GPU.
{ .lead }

## Requirements

- Linux or macOS (Windows through WSL2).
- [uv](https://docs.astral.sh/uv/), which installs Python 3.12 for you if it is missing.
- git.

## Steps

```bash
git clone https://github.com/StardustModulator/benchtop-lab.git
cd benchtop-lab
uv sync --all-packages --all-groups
uv run benchtop --version
```

The last command prints the installed version:

```text
benchtop 0.1.0.dev0
```

??? question "What did `uv sync` just do?"

    It created a virtual environment in `.venv/`, installed the six `benchtop-*` packages in editable mode,
    and installed the developer tools (tests, linters, this docs site) at the exact versions recorded in
    `uv.lock`. Nothing was installed outside the repository folder.

## Choosing a PyTorch build

PyTorch is optional at this stage. When a project needs it, pick **one** build:

=== "CPU only"

    ```bash
    uv sync --all-packages --all-groups --extra cpu
    ```

    A small download that runs everywhere. Projects P0–P3 and P7 are designed for it.

=== "NVIDIA GPU (CUDA 12.6)"

    ```bash
    uv sync --all-packages --all-groups --extra cu
    ```

    Needed only for the vision and language projects (P4–P6), which also fit free Colab and Kaggle GPUs.

The two builds conflict, so uv refuses to install both.

## Check your work

```bash
uv run pytest -q
```

Every test should pass. If one fails on a fresh clone, that is a bug:
[open an issue](https://github.com/StardustModulator/benchtop-lab/issues/new/choose) and include the output.

!!! info "Coming in milestone M0"

    `benchtop doctor` will check Python, MuJoCo offscreen rendering, LeRobot, ffmpeg, disk space and your
    PyTorch device, and print a fix for anything that fails.
