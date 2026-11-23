<!-- SPDX-FileCopyrightText: 2026 Benchtop Lab contributors -->
<!-- SPDX-License-Identifier: CC-BY-4.0 -->

## What and why

<!-- One or two sentences: what changes, and what problem it solves. Link the issue if there is one (Closes #123). -->

## How it was checked

<!-- The commands you ran and what you saw. Add screenshots (light and dark) for anything a person looks at. -->

## Checklist

- [ ] One logical change, with a [Conventional Commits](https://www.conventionalcommits.org/) title (`feat(sim): …`, `fix(grade): …`, `docs(p3): …`).
- [ ] Tests added or updated. Success checks have positive **and** adversarial tests; bug fixes have a regression test.
- [ ] `make gate` passes (ruff, import-linter, mypy, tests with coverage ≥ 85%).
- [ ] Docs, lessons or docstrings updated where behaviour changed.
- [ ] New files carry an SPDX header (`Apache-2.0` for code, `CC-BY-4.0` for prose).
- [ ] No secrets or tokens, and no compiled binaries (a hook also blocks any file over 1 MB).
- [ ] New dependencies are permissively licensed (Apache-2.0, MIT, BSD, ISC, PSF, MPL-2.0) and explained above.
