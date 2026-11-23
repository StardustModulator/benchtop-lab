---
title: Releasing
description: How Benchtop Lab versions are bumped and how the changelog is generated.
---

<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Releasing

The six packages share one version number, and the changelog is generated from commit messages. Publishing
anything (a git tag, a GitHub release, a PyPI upload) needs the owner's explicit approval, recorded in
[Progress](../PROGRESS.md).
{ .lead }

## One shared version

The version lives in seven places: the workspace root `pyproject.toml` and the `__version__` of each package.
Each package also pins its sibling packages to exactly that version, so an install from PyPI can never mix
releases. `tools/bump_version.py` keeps all of them in step.

```bash
uv run python tools/bump_version.py --check    # verify everything agrees (CI runs this as a test)
uv run python tools/bump_version.py 0.1.0      # write a new version everywhere
uv lock                                        # refresh the lockfile for the new version
```

Versions follow [PEP 440](https://peps.python.org/pep-0440/): `0.1.0.dev0` while a release is in development,
`0.1.0rc1` for a release candidate, `0.1.0` for the release.

## Changelog

Commits follow [Conventional Commits](https://www.conventionalcommits.org/) (`feat(sim): …`, `fix(grade): …`).
[git-cliff](https://git-cliff.org/) groups them into `CHANGELOG.md` using `cliff.toml`:

```bash
uv run git-cliff --output CHANGELOG.md                   # regenerate, newest changes under "Unreleased"
uv run git-cliff --tag v0.1.0 --output CHANGELOG.md      # preview the changelog as release 0.1.0
```

The changelog is regenerated when a release is prepared, not on every pull request. It is shown on this site
under [Project → Changelog](../project/changelog.md).

## Release checklist

1. The owner approves the release, and the approval is recorded in Progress.
2. `bump_version.py <version>`, then `uv lock`.
3. `git-cliff --tag v<version> --output CHANGELOG.md`.
4. Open a pull request with these changes and merge it when CI is green.
5. The owner creates the tag and the GitHub release. Automated publishing to PyPI is planned for the 1.0
   milestone.
