# Architecture Decision Records

Short records of decisions that shape the project. Add a new entry for any change to scope, architecture,
dependencies, thresholds or licensing. Never rewrite an accepted record; supersede it.

Format: `ADR-NNN · Title` — Status (Proposed | Accepted | Superseded by ADR-MMM) — Date — Context — Decision — Consequences.

## ADR-001 · Fully open source, no paid tier
- Status: Accepted — 2026-11-23
- Context: The owner decided this first project is a pure open-source contribution; monetization starts with project #2.
- Decision: No payments, no gated content, no paid tier, no telemetry.
- Consequences: Success is measured by adoption, completions and contributors (PLAN §17).

## ADR-002 · Build on LeRobot 0.7 and its EnvHub/sim-robot contract; never fork
- Status: Accepted — 2026-11-23
- Context: LeRobot 0.7 can run any Gymnasium env following its conventions as a batched eval env or as a sim robot,
  and loads environments from EnvHub folders/Spaces. An official SO-101 MuJoCo Space defines the conventions.
- Decision: Our tasks implement that contract and match the official conventions (30 fps, joint degrees, gripper 0–100,
  cameras `front`/`wrist`, semantics `so101-joint-degrees-v1`). All LeRobot imports go through `benchtop_core.compat`.
- Consequences: Learners use LeRobot's own commands; upstream changes are absorbed in one module.

## ADR-003 · Licenses: Apache-2.0 for code, CC BY 4.0 for content and datasets
- Status: Accepted — 2026-11-23
- Context: Upstream LeRobot, MuJoCo, Menagerie SO-101, mink and SO-ARM100 are Apache-2.0; Gymnasium is MIT.
- Decision: Apache-2.0 for all code (incl. starters and solutions); CC BY 4.0 for lessons, docs, figures and datasets;
  checkpoints Apache-2.0. Graded projects avoid Gemma-licensed weights (π0/π0.5).
- Consequences: SPDX headers on every file; `reuse lint` in CI; vendored assets keep their LICENSE files.

## ADR-004 · uv workspace monorepo with six packages
- Status: Accepted — 2026-11-23 (S01)
- Decision: `benchtop-core`, `benchtop-sim`, `benchtop-grade`, `benchtop-data`, `benchtop-real`, `benchtop-lab`
  (CLI meta-package), released together under one version. Dependency rules in ARCHITECTURE §2, enforced by import-linter.

## ADR-005 · CPU-first curriculum
- Status: Accepted — 2026-11-23
- Context: Many learners have no GPU; Kaggle offers 2× T4 for ~30 h/week to phone-verified accounts.
- Decision: P0–P3 and P7 run on CPU (state-based policies); P4 and P5 are GPU projects sized to ≤ 4 h and P6 to ≤ 6 h
  on one free T4.
- Consequences: P3 uses privileged object state (`environment_state`); vision is introduced in P4.

## ADR-006 · Thresholds use the Wilson 95% lower bound and are calibrated from measurements
- Status: Accepted — 2026-11-23
- Decision: Pass/Merit/Distinction thresholds compare against the Wilson lower bound on exam seeds. Provisional values
  in PLAN §5.3 are replaced in M6 by values measured on reference policies, recorded here.

## ADR-007 · The MLP behavior-cloning policy lives in `benchtop_core.policies`
- Status: Accepted — 2026-11-23
- Context: P3 compares a plain MLP behavior-cloning policy with ACT. LeRobot has no plain MLP policy, but supports
  "bring your own policy" plugins, which must import `lerobot` and `torch`.
- Decision: The plugin lives in `benchtop_core.policies.mlp` (no seventh package). Import-linter allows `lerobot`/`torch`
  imports only in `benchtop_core.compat` and `benchtop_core.policies`.

## ADR-008 · Session merge flow: branch → PR → CI → merge
- Status: Accepted — 2026-11-23
- Decision: Before CI exists (S01), sessions merge to `main` after the local gate. From S02 on, every session pushes
  its branch, opens a PR, waits for CI (`gh pr checks --watch`), and merges with a rebase merge only when CI is green;
  otherwise the PR stays open as a draft with the blocker recorded. The headless runner commits and pushes
  work-in-progress on the session branch when a run is cut off, and the next run resumes that branch.

## ADR-009 · Docs toolchain decided in S04
- Status: Proposed — 2026-11-23
- Context: Material for MkDocs entered maintenance mode in Nov 2025 (critical fixes until May 2027); its authors build
  Zensical as the successor, compatible with `mkdocs.yml`.
- Decision: In S04, adopt Zensical if it supports mermaid, admonitions, tabs and API docs (mkdocstrings or equivalent)
  for our needs; otherwise pin Material 9.x and add a migration task before May 2027.

## ADR-010 · Copyleft developer tools run only as isolated external CLIs
- Status: Accepted — 2026-11-23 (S01)
- Context: PLAN §11 and ADR-003 require `reuse lint`, but the REUSE tool is GPL-3.0-or-later. CLAUDE.md forbids GPL
  dependencies so that nothing we ship, import or lock carries a copyleft obligation.
- Decision: A copyleft tool may be used only as a standalone command that never enters `uv.lock`, is never imported by
  our code and is never vendored: a pre-commit hook in its own isolated environment, or `uvx` in CI/Makefile. REUSE is
  the only such tool today; `pip-licenses` and other checks we import stay permissive. Every dependency in `uv.lock`
  must still pass the permissive/weak-copyleft allowlist.
- Consequences: `reuse lint` runs from `.pre-commit-config.yaml` and `make reuse` (S02 adds it to CI the same way).
  Using the tool does not change the licence of our code, as with git (GPL-2.0) on the same machines.
