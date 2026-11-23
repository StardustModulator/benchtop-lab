---
title: Command line
description: Reference for the benchtop command, generated from the installed command-line interface.
---

<!-- SPDX-License-Identifier: CC-BY-4.0 -->

# Command line

Everything in Benchtop Lab is driven by one command, `benchtop`. This page is generated from the command
itself each time the site is built, so it lists exactly what the code on `main` provides.
{ .lead }

Inside a clone of the repository, prefix commands with `uv run` (for example `uv run benchtop --version`).

## Output and colour

- Output is styled only when it goes to a terminal. Piped or redirected output is plain text.
- Setting `NO_COLOR` to any non-empty value removes all styling ([no-color.org](https://no-color.org)).
- `FORCE_COLOR=1` forces styling, for example in CI logs. `FORCE_COLOR=0` turns it off.

## Commands

<!-- benchtop:cli-reference -->
