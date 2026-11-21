# ARK AI Run1020 — Planner terminal COMMIT outcome matrix

**Work basis:** Draft PR #8 branch `research/jarvis-foundations`, exact HEAD `ff3e9e50ca861486a667bce243ee6ca62af08e28`. This is a test-only child; PR #8 remains OPEN/DRAFT/UNMERGED.

## Finding

The Planner journal already rejects stale revisions and treats recovered `RUNNING` as ambiguous. Existing COMMIT-UNKNOWN coverage exercises both a native commit whose acknowledgement is lost and a pre-COMMIT result-construction failure. This package isolates the SQLite `commit()` call itself for a terminal `RUNNING → FAILED` transition.

## Regression

The new parameterized test injects two distinct outcomes at the same COMMIT boundary:

- **Before native COMMIT:** the synthetic connection rolls back and raises. Cold recovery must retain `RUNNING`, leave its dependent step `PENDING`, and preserve the independent step.
- **After native COMMIT:** the synthetic connection commits and then loses the acknowledgement. Cold recovery must retain terminal `FAILED`, block only its dependent step, and preserve the independent step.

Both paths check the exact event sequence, SQLite `quick_check`, and false-only dispatch/replay flags. The committed outcome also rejects a stale retained tail rather than appending a duplicate terminal event.

The test is authored; no local pytest/Ruff PASS is claimed. Exact-head Ubuntu/Windows × Python 3.11–3.13 CI is required.

## Limits

Synthetic PlanStep/ToolCall values and disposable local SQLite only. This does not execute a ToolBackend, resolve a real external outcome, provide trusted time or independent custody, prove power-loss/fsync durability, or authorize automatic replay. No production source, frozen contract, Candidate, protected evaluation, UI, PR #5, PR #9, or main branch is changed.
