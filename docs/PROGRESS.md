# Progress

Updated at the end of every Claude Code session (see [CLAUDE.md](https://github.com/StardustModulator/benchtop-lab/blob/main/CLAUDE.md)). Newest session log entry first.
Times are IST (Asia/Kolkata, UTC+5:30).

## Status

| | |
| --- | --- |
| Phase | 2: plan complete, build not started |
| Current milestone | M0 Foundations |
| Next session | **S01 · Monorepo skeleton and quality tooling** |
| Sessions done | 0 / 70 (+ 0 contingency used of ~7) |
| Percent complete | 0% |
| Estimated sessions remaining | 70 |
| Estimated days remaining | ~31 (range 26–39; 77 sessions incl. contingency at ~2.5 effective sessions/day) |
| Last green `main` commit | planning docs (Phase 2) |

## Milestones

| Milestone | Sessions | Done | Status |
| --- | --- | --- | --- |
| M0 Foundations | S01–S04 | 0/4 | not started |
| M1 Sim core | S05–S09 | 0/5 | not started |
| M2 Task suite | S10–S16 | 0/7 | not started |
| M3 Experts and demos | S17–S22 | 0/6 | not started |
| M4 Grader | S23–S30 | 0/8 | not started |
| M5 Dataset doctor | S31–S35 | 0/5 | not started |
| M6 Reference baselines | S36–S40 | 0/5 | not started |
| M7 Projects P0–P4 | S41–S50 | 0/10 | not started |
| M8 Projects P5–P7 | S51–S57 | 0/7 | not started |
| M9 Hardware path | S58–S62 | 0/5 | not started |
| M10 Hardening and v1.0 | S63–S70 | 0/8 | not started |

## Blockers and decisions waiting on Shiva

| ID | Item | Needed by |
| --- | --- | --- |
| D1 | Confirm the name "Benchtop Lab" (renaming later is cheap until S04, costly after) | S04 |
| D7 | Allow branch protection on `main` (no force-push, require CI) and drop the unused `delete_repo` scope from the build machine's GitHub login | S02 |
| D2 | Free Kaggle account for GPU reference runs (optional) | S40 |
| D3 | Hugging Face account/org for EnvHub Spaces, datasets, checkpoints (optional) | S36 |
| D4 | PyPI account for Trusted Publishing of `benchtop-lab` (optional) | S70 |
| D5 | Access to a real SO-101 (optional) | S62 |
| D6 | Contact email for conduct/security reports (optional) | S70 |

## Ideas and follow-ups (not in the current plan)

- (empty)

## Session log

<!--
Template for each entry (newest first):

### SNN · <title> — <DONE | PARTIAL | BLOCKED>
- Date (IST): YYYY-MM-DD HH:MM–HH:MM
- Branch / PR: session/SNN-slug → merged to main in <sha> | PR #<n> (tests failing: <why>)
- Done:
  - ...
- Tests: <passed>/<total>, coverage <x>%, `ruff`/`mypy` clean
- Next: SNN+1 <title> (or: resume SNN at task <k>)
- Blockers: none | <what, who can unblock>
- Notes for next session: <context that would otherwise be lost>
- Usage: stopped early due to usage limit? yes/no
-->

### Phase 2 · Planning — DONE
- Date (IST): 2026-11-23
- Done: research, PLAN.md, ARCHITECTURE.md, MILESTONES.md, CLAUDE.md, `.claude/` agents/commands/skills, licenses,
  community files.
- Next: S01 Monorepo skeleton and quality tooling.
- Blockers: none.
