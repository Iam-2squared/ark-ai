# Run1440 — PlannerJournal diamond recovery with a RUNNING sibling

## Exact basis

- Parent: Draft PR #8, branch \`research/jarvis-foundations\`.
- Exact parent work-basis HEAD: \`5a344d250dd0ef2a208ccd09f5d791b10c548bbe\`.
- Child branch: \`research/run1440-planner-journal-diamond-running-barrier-20261126\`.
- Regression test: \`tests/test_planner_journal_diamond_running_barrier_run1440.py\`.

## Coverage

Exercises the production \`PlannerJournal\` plus exact \`PlanGraph\` across cold recovery:

1. Root succeeds.
2. Both diamond branches enter RUNNING.
3. One branch fails; its pending fan-in join and leaf become terminal BLOCKED.
4. Cold recovery preserves the other branch as ambiguous RUNNING while retaining the blocked join/leaf.
5. Attempting to run the blocked join is rejected.
6. The remaining RUNNING branch may later succeed, but it cannot resurrect the already-blocked join.

The test also verifies that an unrelated independent step remains PENDING and that recovery never reports dispatch or automatic replay authority.

## Boundaries

- Test-only; PlannerJournal v1 DDL, event hash, CAS semantics, PlanStep/ToolCall contracts and production source are unchanged.
- Synthetic plan data only. No ToolBackend, registry dispatch, external effect, trusted clock, consent, or automatic retry.
- This is focused regression evidence, not a claim of complete planner crash recovery or production execution readiness.
- Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff result is claimed.

No paid/external compute, credentials, hardware, destructive operation, main write/merge, V3 preflight/training, protected evaluation, Candidate action, or UI/frontend work occurred. PR #8 remains Draft/unmerged.
