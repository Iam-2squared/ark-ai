# Run1221 — Planner journal COMMIT-UNKNOWN and hard-exit recovery on current foundation

## Exact basis

- Repository: `Iam-2squared/ark-ai`.
- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `15d983ded8efe7df0b80e1d5c0b1e44d4c8caf93`.
- Rebased test-only source: Draft PR #384, `research/run1200-planner-journal-commit-unknown-tests`, exact child HEAD `3dbf5a4916769870496b2dc122d307305378084d`.
- Predecessor CI [45209036283](https://github.com/Iam-2squared/ark-ai/actions/runs/45209036283) had five GREEN jobs; Windows Python 3.13 failed in the unrelated paused UI test `tests/ui/test_server.py::test_write_requires_process_token_and_origin[headers0]` with a socket `ConnectionAbortedError` after 19,338 passed and 151 skipped. No UI source/test change is made here; fresh exact-head CI is required.
- New child branch: `research/run1221-planner-journal-commit-unknown-rebase`.

## Coverage

The synthetic SQLite fixture injects both native outcomes behind a lost Planner journal COMMIT acknowledgement:

- native ROLLBACK followed by an acknowledgement exception; cold recovery must retain genesis with no event;
- native COMMIT followed by an acknowledgement exception; cold recovery must observe exactly one event and preserve the step as RUNNING/ambiguous.

Both paths require exactly one COMMIT attempt, no returned receipt, no automatic retry, valid SQLite `quick_check`, no stored ToolCall argument fixture, and no dispatch/replay authority.

A spawned child process then performs a local journal transition and calls `os._exit` immediately after native COMMIT but before the transition can return its receipt or execute Python cleanup. A fresh parent-process journal must recover the committed RUNNING step as ambiguous, with no ready work and no automatic replay.

## Evidence limits

Synthetic local SQLite only. This does not prove fsync/power-loss durability, independent custody, trusted time, authenticated consent, external backend completion, cross-store atomicity, or exactly-once external effects. RUNNING remains ambiguous; the journal never authorizes dispatch or replay.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed. No paid/external compute, Candidate, protected V2 evaluation, credentials, hardware, destructive action, frozen-contract change, UI/frontend work or main merge. PR #5/#8/#9 remain Draft/unmerged and untouched by this child. ARK/JARVIS remains NOT_PASSED.
