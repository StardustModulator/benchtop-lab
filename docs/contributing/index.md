---
title: Contributing
description: How to report problems, propose tasks and send changes to Benchtop Lab.
---

<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Contributing

Benchtop Lab is free and open source, and every kind of contribution helps: fixing a typo in a lesson, reporting
a confusing step, adding a task or a debugging-clinic case.
{ .lead }

The complete guide is
[CONTRIBUTING.md](https://github.com/StardustModulator/benchtop-lab/blob/main/CONTRIBUTING.md) in the
repository. This page is the short version.

## Ways to help

| You want to… | Do this |
| --- | --- |
| Report a bug | Open an issue with the [Bug form](https://github.com/StardustModulator/benchtop-lab/issues/new/choose) |
| Say a lesson was confusing | Open an issue with the Lesson feedback form, naming the project and section |
| Propose a task, project or clinic case | Open an issue with the Task proposal form before writing code |
| Report a security problem | Do not open an issue. Follow the [security policy](https://github.com/StardustModulator/benchtop-lab/blob/main/SECURITY.md) |
| Fix something small | Send a pull request directly |

Everyone taking part follows the
[Code of Conduct](https://github.com/StardustModulator/benchtop-lab/blob/main/CODE_OF_CONDUCT.md).

## Set up and check your change

```bash
git clone https://github.com/StardustModulator/benchtop-lab.git
cd benchtop-lab
uv sync --all-packages --all-groups
uv run pre-commit install
```

Before opening a pull request, run the same checks that continuous integration runs:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run lint-imports
uv run pytest -q --cov --cov-fail-under=85
uv run mkdocs build --strict   # if you touched docs or docstrings
```

## Rules worth knowing

- **Build on LeRobot, do not fork it.** Only the compatibility layer imports `lerobot`.
- **The [SO-101 conventions](../start/conventions.md) are fixed.**
- **Measure honestly.** Do not weaken a check to make a policy pass.
- **No global random state.** Every random draw comes from an explicit seed.

## More

- [Writing docs](writing-docs.md): how pages on this site are written and checked.
- [Releasing](releasing.md): how versions and the changelog are produced.

## Licence of contributions

Code is contributed under Apache-2.0 and written content under CC&nbsp;BY&nbsp;4.0, the same as the rest of the
project. No contributor licence agreement is required.
