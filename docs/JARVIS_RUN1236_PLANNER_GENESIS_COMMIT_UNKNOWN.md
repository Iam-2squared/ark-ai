# Run1236 — Planner journal genesis COMMIT-UNKNOWN recovery

## Exact basis

- Repository: `Iam-2squared/ark-ai`.
- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent HEAD: `36a1c947196efb26a0328b25c516054e80a77536`.
- Child branch: `research/run1236-planner-genesis-commit-unknown`.
- Test-only addition; Planner journal source, schema, PlanStep/ToolCall contracts and V1/V2 freezes remain unchanged.

## Coverage

The synthetic SQLite boundary injects acknowledgement loss at the initial `create_plan` genesis COMMIT in both possible outcomes:

- native rollback before raising: a cold journal reports the plan as not found, with no metadata or event rows;
- native commit before raising: a cold journal recovers exactly the all-PENDING genesis state, and a duplicate create is rejected.

Both paths assert exactly one COMMIT attempt, SQLite quick-check integrity and absence of raw ToolCall argument text from the journal file. No transition is retried and no dispatch or automatic replay authority is created.

## Evidence boundary

This covers local SQLite COMMIT acknowledgement ambiguity for Planner genesis only. It does not prove fsync/power-loss durability, cross-device atomicity, trusted time, consent, tool execution, or external exactly-once effects. Synthetic fixtures only. No paid/external compute, credentials, hardware, UI work, Candidate generation, protected V2 evaluation, frozen-contract change or main merge. PR #8 remains Draft/unmerged and ARK/JARVIS remains NOT_PASSED.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no local test or CI result is claimed here.
