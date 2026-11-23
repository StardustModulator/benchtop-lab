# Contributing to Benchtop Lab

Thank you for helping make robot learning easier to learn. Benchtop Lab is free and open source, and every kind of
contribution helps: fixing a typo in a lesson, reporting a confusing step, adding a task, a doctor check or a
debugging-clinic case.

By participating you agree to follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## Ways to contribute

| You want to… | Start here |
| --- | --- |
| Report a bug | Open an issue with the **Bug** template. Include `benchtop doctor --json` output. |
| Say a lesson was confusing | Open an issue with the **Lesson feedback** template, naming the project and section. |
| Propose a new task, project or clinic case | Open an issue with the **Task proposal** template first; we agree on scope before code. |
| Report a security problem | Do not open an issue. Follow [SECURITY.md](SECURITY.md) to report it privately. |
| Fix something small | Send a pull request directly. |
| Share your report card | Post it in Discussions → Show and tell, or open a PR adding it to the gallery page. |

Issues labelled `good first issue` are scoped for newcomers.

## Development setup

Requirements: Python 3.12+, [uv](https://docs.astral.sh/uv/), git, and for rendering tests an OpenGL backend
(Linux: `sudo apt install libegl1 libgl1 libosmesa6`).

```bash
git clone https://github.com/StardustModulator/benchtop-lab.git
cd benchtop-lab
uv sync --all-packages --all-groups
uv run pre-commit install
uv run pytest -q
```

> `make setup` runs the first two commands, `make gate` runs ruff, mypy, import-linter and the tests, and
> `make help` lists every target. `make` is optional: every target is a thin wrapper over the `uv run` commands.

## Continuous integration

Every pull request runs the same gate on GitHub Actions ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)):
ruff, import-linter, file hygiene and `actionlint`, `mypy --strict`, the tests on Python 3.12 and 3.13 with the
85% coverage gate, the `slow` and `render` suites, `reuse lint`, and a `gitleaks` scan of the whole history. A pull
request merges only when the **CI passed** check is green. A nightly workflow repeats the tests on Linux and macOS.

If you edit a workflow: pin every action to a full commit SHA with the version in a trailing comment
(`uses: owner/action@<40-character sha> # v1.2.3`), keep `permissions:` read-only unless a job truly needs more, and
run `uv run pre-commit run actionlint --all-files`. `tests/test_ci_config.py` checks these rules.

## Pull request checklist

- [ ] One logical change per PR, with a clear title in [Conventional Commits](https://www.conventionalcommits.org/)
      form (`feat(sim): …`, `fix(grade): …`, `docs(p3): …`).
- [ ] Tests added or updated. Success checks need positive **and** adversarial tests. Bug fixes need a regression test.
- [ ] `uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run lint-imports && uv run pytest -q` pass.
- [ ] Docs updated (lessons, CLI reference, or docstrings) and `uv run mkdocs build --strict` passes if you touched docs.
- [ ] New files carry an SPDX header (`Apache-2.0` for code, `CC-BY-4.0` for lesson text).
- [ ] No secrets, tokens or large binaries (> 1 MB) committed. Datasets and checkpoints go to the Hugging Face Hub, not git.
- [ ] New dependencies have a permissive or weak-copyleft license (Apache-2.0, MIT, BSD, ISC, PSF, MPL-2.0; never GPL/AGPL) and a reason in the PR description.

## Design rules worth knowing

- **Build on LeRobot, do not fork it.** Only `benchtop_core.compat` (and the `benchtop_core.policies` plugin) import `lerobot`.
- **SO-101 conventions are fixed**: joint names and order, degrees, gripper 0–100, 30 fps, cameras `front`/`wrist`.
- **Honest measurement**: grading uses held-out exam seeds and the Wilson 95% lower bound. Don't weaken a check to make
  a policy pass; fix the policy or open a discussion about the check.
- **Determinism**: no global RNG; every random draw derives from an explicit seed.

The full spec is in [docs/PLAN.md](docs/PLAN.md) and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). Significant
changes need an entry in [docs/DECISIONS.md](docs/DECISIONS.md).

## Licensing of contributions

By submitting a contribution you agree that your code is licensed under the [Apache License 2.0](LICENSE) and your
written content (lessons, docs, figures) under [CC BY 4.0](LICENSE-CONTENT), the same as the rest of the project
(inbound = outbound). No CLA is required. Please only contribute work you have the right to license this way.

## AI-assisted contributions

Much of this project is built with AI coding assistants under human review. AI-assisted contributions are welcome if
you have reviewed and tested them yourself and can explain every line.
