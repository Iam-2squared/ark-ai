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
