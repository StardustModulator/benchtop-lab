---
description: Execute the next planned build session from docs/MILESTONES.md, end to end
argument-hint: "[optional session id, e.g. S07, or 'resume']"
---

Execute one Benchtop Lab build session. Requested session: $ARGUMENTS (if empty, use the next session in docs/PROGRESS.md).

Follow the "Session protocol" in CLAUDE.md exactly. Concretely:

1. Orient as CLAUDE.md "Working efficiently" says: `docs/PROGRESS.md` status table, blockers and the latest
   session-log entry ("Notes for next session"); only this session's section of `docs/MILESTONES.md`; only the
   sections of `docs/PLAN.md` and `docs/ARCHITECTURE.md` it cites (find them with `grep -n '^#'`).
2. If a blocker in PROGRESS.md prevents this session, do not start it: write a BLOCKED entry explaining why and stop.
3. Sync `main`. If `origin/session/<id>-*` exists, check it out and resume; otherwise create `session/<id>-<slug>`.
   Write a todo list mapping 1:1 to the session's Tasks and Acceptance. Commit and push after each completed task.
4. Implement with tests. Keep scope tight. Use the `test-runner` subagent to run and triage the gate, and the
   `reviewer` subagent once to review the full diff (`git diff main...HEAD`) before finishing. Fix every "must fix",
   re-run the gate, and only call `reviewer` again if a fix changed the design.
   If the session touches any user interface (docs site, HTML reports, charts, CLI output, landing page), load the
   `ui-excellence` skill first, follow its tokens and verification steps, and have `reviewer` apply its checklist.
5. For milestone-final sessions, also ask `reviewer` to review the whole milestone; for lesson sessions, also run
   `curriculum-reviewer`.
6. Update `docs/PROGRESS.md` (status table, milestone row, percent complete = planned sessions done / 70 (contingency
   sessions `S##x` are tracked separately), nights remaining = sessions left ÷ 6 (nightly 23:00–07:00 IST runs; see
   MILESTONES.md "Estimate and schedule"),
   new session-log entry at the top with notes for the next session). Update `docs/DECISIONS.md` if any design changed.
7. Merge per CLAUDE.md step 8 (ADR-008): S01 fast-forwards after the local gate; from S02 on, PR → CI green →
   `gh pr merge --rebase --delete-branch`. Anything red → draft PR + blocker in PROGRESS.md.
8. Print the final summary block:

```
SESSION: <id> <title>
RESULT: DONE | PARTIAL | BLOCKED
MAIN: <commit sha> | PR: <url>
TESTS: <passed>/<total> (slow: <passed>/<total>)
NEXT: <next session id and title>
NEEDS FROM OWNER: <none | list>
```

Never publish packages, push to the Hugging Face Hub, post anywhere, or spend money. Never commit secrets.
If you approach the usage limit, stop cleanly as described in CLAUDE.md "Usage limits".
