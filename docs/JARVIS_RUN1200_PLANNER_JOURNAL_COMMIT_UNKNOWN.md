# Run1200 — Planner journal COMMIT ambiguity and hard-exit recovery

## Exact basis

- Parent: Draft PR #381, branch \`research/run1197-planner-durable-journal-rebase\`.
- Exact parent HEAD: \`5272d6d9689d7adbf3c11e48fecf8da23e789cf5\`.
- Parent exact-head CI run [45199241648](https://github.com/Iam-2squared/ark-ai/actions/runs/45199241648) was GREEN (6/6 Windows/Linux × Python 3.11–3.13 jobs).
- Child branch: \`research/run1200-planner-journal-commit-unknown-tests\`.
- Focused test commit: \`02b608192f79ac4aa996a3d31569922b585d4bcc\`.
- This is a test-only dependent child; Planner production source, schema and frozen contracts are unchanged.

## Coverage

The first synthetic SQLite test injects both possible native outcomes behind a lost COMMIT acknowledgement:
- native ROLLBACK followed by an acknowledgement exception; cold recovery must retain genesis with no event;
- native COMMIT followed by an acknowledgement exception; cold recovery must observe exactly one event and preserve the step as RUNNING/ambiguous.

Both paths require exactly one COMMIT attempt, no returned receipt, no automatic retry, a valid SQLite quick_check, no stored ToolCall argument fixture, and no dispatch/replay authority.

A spawned child process then performs a real local journal transition and calls \`os._exit\` immediately after native COMMIT but before the transition can return its receipt or execute Python cleanup. A fresh parent-process journal must recover the committed RUNNING step as ambiguous, with no ready work and no automatic replay.

## Evidence limits

These are synthetic local SQLite transaction/process-crash fixtures. They do not prove fsync/power-loss durability, independent custody, trusted time, authenticated consent, external backend completion, cross-store atomicity, or exactly-once external effects. RUNNING remains ambiguous; the journal never authorizes dispatch or replay.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required on this child. No local pytest/Ruff PASS is claimed. No paid/external compute, Candidate, protected V2 evaluation, credentials, hardware, destructive operation, frozen-contract change, UI/frontend work or main merge is involved. PR #5, #8, #9 and #381 remain untouched; PR #381 remains Draft/unmerged. ARK/JARVIS remains NOT_PASSED.
