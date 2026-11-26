# Run1456 — Planner terminal COMMIT with a surviving WAL reader

**Parent:** Draft PR #638, branch `research/run1450-planner-audit-native-commit-hard-exit-20261126`.
**Exact parent work-basis HEAD:** `4f57e4c282cd739d7bf2453177e1430f7e4c12d4`.
**Child:** `research/run1456-planner-terminal-wal-reader-hard-exit-20261126`.

## Scenario

The test creates a synthetic three-step PlanGraph, commits the root step as RUNNING, and pins an independent SQLite read snapshot of that journal frontier. A spawned writer then recovers the plan and transitions the root to FAILED. Its connection wrapper exits the process immediately after native COMMIT returns, before cleanup or a transition receipt.

The keeper must continue to see the pre-terminal sequence while the writer is gone. TRUNCATE checkpoint remains incomplete until the keeper closes. Cold recovery must then replay the committed terminal event through the existing PlanGraph policy: root FAILED, dependent BLOCKED, independent PENDING. A stale pre-terminal graph cannot append another transition. Dispatch and automatic replay remain denied.

## Scope and evidence

Synthetic PlanGraph values and disposable local SQLite only. No PlannerJournal production source, schema v1 DDL, event/hash format, transition policy, public API, or frozen contract changes.

This is native-COMMIT process-exit plus surviving-reader/last-close regression evidence. It is **not** fsync/power-loss durability, independent custody, trusted time, authenticated consent, cross-store atomicity, or exactly-once external effects. A recovered RUNNING step remains ambiguous and is never automatically replayed.

No paid/external compute, credentials, hardware, Candidate, protected V2 evaluation, main write/merge, or UI/frontend work occurred. PR #8 and PR #638 remain Draft/unmerged. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no PASS is claimed.
