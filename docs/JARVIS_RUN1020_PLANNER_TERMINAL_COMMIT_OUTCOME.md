# ARK AI Run1020 — Planner terminal COMMIT outcome matrix

**Rebase work basis:** Draft PR #8 branch `research/jarvis-foundations`, exact HEAD `e53ffc7db904584a1e817fcfb544012d75eeafc0`. Rebased from PR #94's test-only package; PR #8 remains OPEN/DRAFT/UNMERGED.

## Finding

The Planner journal already rejects stale revisions and treats recovered `RUNNING` as ambiguous. Existing COMMIT-UNKNOWN coverage exercises both a native commit whose acknowledgement is lost and a pre-COMMIT result-construction failure. This package isolates the SQLite `commit()` call itself for a terminal `RUNNING → FAILED` transition.

## Regression

The parameterized test injects two distinct outcomes at the same COMMIT boundary:

- **Before native COMMIT:** the synthetic connection rolls back and raises. Cold recovery must retain `RUNNING`, leave its dependent step `PENDING`, and preserve the independent step.
- **After native COMMIT:** the synthetic connection commits and then loses the acknowledgement. Cold recovery must retain terminal `FAILED`, block only its dependent step, and preserve the independent step.

Both paths check the exact event sequence, SQLite `quick_check`, and false-only dispatch/replay flags. The committed outcome also rejects a stale retained tail rather than appending a duplicate terminal event.

The original package passed exact-head CI run #44731076172 (6/6) on its earlier base. This rebased head requires its own exact-head CI; no PASS is transferred. No local pytest/Ruff PASS is claimed.

## Limits

Synthetic PlanStep/ToolCall values and disposable local SQLite only. This does not execute a ToolBackend, resolve a real external outcome, provide trusted time or independent custody, prove power-loss/fsync durability, or authorize automatic replay. No production source, frozen contract, Candidate, protected evaluation, UI, PR #5, PR #9, or main branch is changed.


## Run1030 rebase onto the current foundation head

- New exact work basis: Draft PR #8 branch `research/jarvis-foundations`, HEAD `b585c61a6e3ca1a9f456175b2a96053a908a500c`.
- Re-applied as a test-only child after the PR #8 checkpoint commit; no production source or frozen contract is changed.
- Previous child PR #99 head `f1f32cc2d76c4e8b7dd44e89dbcf619aa84a7473` had exact-head CI run #44796135254 GREEN (6/6). That evidence applies only to the previous head and is not transferred to this new rebase.
- Fresh exact-head six-job CI is required. No local pytest/Ruff PASS is claimed.


## Run1031 rebase onto the latest foundation checkpoint

- Exact work basis: Draft PR #8 branch `research/jarvis-foundations`, HEAD `7d25d985c613a36bf81bf4fa11c0fbaea4928b11` (the Run1030 checkpoint commit).
- Re-applied as a test-only child. Production source, frozen contracts and main are unchanged.
- Previous Run1030 rebase head `794b418b4596a4ddf1b84529638ce1cf53b8a556` passed exact-head CI #44804643519 (6/6) on its earlier base. That result is historical and is not transferred to this new head.
- Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed.


## Run1032 rebase onto the latest foundation checkpoint

- Exact work basis: Draft PR #8 branch `research/jarvis-foundations`, HEAD `7e7d737195229154775d06baa5b1d8e5c230882b` (the Run1031 checkpoint-result HEAD).
- Re-applied as a test-only child; Planner source, PlanStep/ToolCall v1, frozen contracts and main are unchanged.
- Previous Run1031 child head `02f076acbabae99d8abef94472e9acbf3efd38c8` passed exact-head CI #44814258160 (6/6) on its earlier base. That result is historical and is not transferred to this rebase.
- Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed.
