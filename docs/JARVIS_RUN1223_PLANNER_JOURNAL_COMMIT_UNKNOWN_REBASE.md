# Run1223 — Planner journal COMMIT-UNKNOWN and hard-exit recovery on latest foundation

## Exact basis

- Repository: `Iam-2squared/ark-ai`.
- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `ef021d9f75de06078674d6b4ba6c31dfce1f2b33`.
- Rebased test-only source: prior Draft PR #405, `research/run1221-planner-journal-commit-unknown-rebase`, exact child HEAD `a2df7a92a7c6abe69f20ebb933edd827aa65967c`.
- Source exact-head CI [45264078094](https://github.com/Iam-2squared/ark-ai/actions/runs/45264078094) was GREEN 6/6 on the predecessor child only; it does not transfer to this rebase.
- New child branch: `research/run1223-planner-journal-commit-unknown-latest`.

## Coverage

The synthetic SQLite fixture injects both native outcomes behind a lost Planner journal COMMIT acknowledgement:

- native ROLLBACK followed by an acknowledgement exception; cold recovery must retain genesis with no event;
- native COMMIT followed by an acknowledgement exception; cold recovery must observe exactly one event and preserve the step as RUNNING/ambiguous.

Both paths require exactly one COMMIT attempt, no returned receipt, no automatic retry, valid SQLite `quick_check`, no stored ToolCall argument fixture, and no dispatch/replay authority.

A spawned child process then performs a local journal transition and calls `os._exit` immediately after native COMMIT but before the transition can return its receipt or execute Python cleanup. A fresh parent-process journal must recover the committed RUNNING step as ambiguous, with no ready work and no automatic replay.

## Evidence limits

Synthetic local SQLite only. This does not prove fsync/power-loss durability, independent custody, trusted time, authenticated consent, external backend completion, cross-store atomicity, or exactly-once external effects. RUNNING remains ambiguous; the journal never authorizes dispatch or replay.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed. No paid/external compute, Candidate, protected V2 evaluation, credentials, hardware, destructive action, frozen-contract change, UI/frontend work or main merge. PR #5/#8/#9 remain Draft/unmerged and untouched. ARK/JARVIS remains NOT_PASSED.
