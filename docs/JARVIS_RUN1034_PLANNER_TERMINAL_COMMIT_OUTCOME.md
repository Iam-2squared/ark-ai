# ARK AI Run1034 — Planner terminal COMMIT outcome matrix (checkpoint rebase)

## Exact work basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent HEAD at this child creation: `07f0e39f47a83721e1a2e4028bedbcb7a997154f`, after PR #134's exact-head GREEN test-only integration.
- Reapplies PR #127's existing synthetic test-only COMMIT-boundary regression. Planner source, PlanStep/ToolCall v1, frozen contracts, main and UI are unchanged.
- Previous PR #127 child head: `cb253476d94fcf2391e11797e4cdf7e1295f9d34`, based on the older PR #8 parent `c92ef6d65df5e79349e3fa534902117bdfcf263b`. Its prior CI does not transfer to this rebase.

## Regression

The parameterized test injects two outcomes at the SQLite `commit()` boundary for a terminal `RUNNING → FAILED` transition:

- **Before native COMMIT:** the synthetic connection rolls back and raises. Cold recovery must retain `RUNNING`, leave its dependent step `PENDING`, and preserve independent work.
- **After native COMMIT:** the synthetic connection commits and then loses the acknowledgement. Cold recovery must retain terminal `FAILED`, block only its dependent step, and preserve independent work.

Both paths verify the exact event sequence, SQLite `quick_check`, and false-only dispatch/replay flags. The committed outcome also rejects a stale retained tail rather than appending a duplicate terminal event.

## Validation

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required for this parent. No local pytest/Ruff PASS is claimed and no old-base CI result is transferred.

## Limits

Synthetic PlanStep/ToolCall values and disposable local SQLite only. This does not execute a ToolBackend, resolve a real external outcome, provide trusted time or independent custody, prove power-loss/fsync durability, or authorize automatic replay. No production source, frozen contract, Candidate, protected evaluation, UI, PR #5, PR #9, or main branch is changed.
