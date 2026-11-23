# Run1223 — Planner journal COMMIT-UNKNOWN and hard-exit recovery on latest foundation

## Exact basis

- Repository: `Iam-2squared/ark-ai`.
- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `0f4343ff36f23b1acb7ae1907b1be5ea98556c0d`.
- Rebased test-only source: Draft PR #407 exact child HEAD `79b8cc4c09878937cc9ee16cedd940da09c6e7a3`.
- Source exact-head CI [45272408600](https://github.com/Iam-2squared/ark-ai/actions/runs/45272408600) was GREEN 6/6 on the predecessor child only; it does not transfer to this rebase.
- New child branch: `research/run1227-planner-commit-unknown-latest`.

## Coverage

The synthetic SQLite fixture injects both native outcomes behind a lost Planner journal COMMIT acknowledgement:

- native ROLLBACK followed by an acknowledgement exception; cold recovery must retain genesis with no event;
- native COMMIT followed by an acknowledgement exception; cold recovery must observe exactly one event and preserve the step as RUNNING/ambiguous.

Both paths require exactly one COMMIT attempt, no returned receipt, no automatic retry, valid SQLite `quick_check`, no stored ToolCall argument fixture, and no dispatch/replay authority.

A spawned child process then performs a local journal transition and calls `os._exit` immediately after native COMMIT but before the transition can return its receipt or execute Python cleanup. A fresh parent-process journal must recover the committed RUNNING step as ambiguous, with no ready work and no automatic replay.

## Evidence limits

Synthetic local SQLite only. This does not prove fsync/power-loss durability, independent custody, trusted time, authenticated consent, external backend completion, cross-store atomicity, or exactly-once external effects. RUNNING remains ambiguous; the journal never authorizes dispatch or replay.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed. No paid/external compute, Candidate, protected V2 evaluation, credentials, hardware, destructive action, frozen-contract change, UI/frontend work or main merge. PR #5/#8/#9 remain Draft/unmerged and untouched. ARK/JARVIS remains NOT_PASSED.
