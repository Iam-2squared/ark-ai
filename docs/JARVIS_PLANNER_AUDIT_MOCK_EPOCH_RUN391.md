# ARK JARVIS foundations — Planner state, Audit continuity and mock cross-store epoch (Run 391)

> Scope: **opt-in, disconnected, FREE-only local synthetic safety infrastructure**, never a live action gateway. This document is not a PASS certificate. It does not modify any frozen V1/V2/UI/Launcher evidence, Memory v1 DDL, V3 approval gate, or protected evaluation.

## 1. Planner in-process status custody

`src/ark/agency/planner.py` now preserves an independent snapshot of the internal `_status` mapping identity and each `PlanStepStatus` carrier/state/revision. `statuses()`, `ready_steps()`, `status_digest()` (through `statuses()`), and `transition()` refuse reflected changes that were not made through a successful Planner transition. An authorized transition refreshes the private witness **after** its terminal cascade, and a failed transition does not publish an updated witness.

This closes the offline review gap where a caller could directly mutate a frozen internal status to `SUCCEEDED` and then obtain an apparently runnable dependent step without any Planner transition. **This is a local tamper signal, not an access-control sandbox against code capable of rewriting both internal state and the private witness.** A genuine JARVIS operation still requires durable journal replay, explicit approval, a trustworthy clock, a validated backend and external effect reconciliation.

Existing high-revision tests require an otherwise-unreachable SQLite `2**63-1` revision as a **synthetic boundary fixture**. Those tests now explicitly rebaseline the private in-process epoch after arranging their offline fixture, then preserve their original overflow/atomic-cascade assertions. Production Planner code has no automatic rebaseline on drift, and the new regressions reject unacknowledged private state forgery.

Focused regression: `tests/test_planner_internal_status_epoch_run391.py` (11 cases).

## 2. Audit continuity read epoch

`src/ark/agency/audit_continuity_review.py` now binds the exact `SQLiteActionAudit.path` object before opening an existing read-only SQLite source, then checks source and retained prior witness values after schema checks, after reading the snapshot, and at every event-hydration/hash phase. A same-text Path replacement or a witness swap detected during one phase is refused before a later callback can restore it. The SQLite schema contract and event-chain hash format are unchanged.

This detects **reflected local object drift**, not OS-level inode replacement or all ABA mutations. SQLite's read transaction pins its own consistent file view but neither signs the log nor authenticates who wrote the rows. Independent retained witnesses remain essential to detect a coordinated local suffix rewrite.

Focused regression: `tests/test_audit_continuity_epoch_run391.py` (6 cases).

## 3. Disconnected mock cycle across durable phases

`src/ark/agency/synthetic_mock_action_cycle_review.py` pins the original ToolCall, one-shot fixture token, Planner topology carriers and SQLite source Path objects before registry resolution. The invariant is rechecked after read-only recovery, durable RUNNING append, synthetic reservation, pre-action audit, optional synthetic sidecar link, and mock-only final SUCCEEDED append. Reservation receipt fields also remain pinned after reservation. No `ToolBackend.execute()` path is called.

The Planner Journal, reservation ledger, ActionAudit and optional link sidecar remain **different SQLite transactions**. A failure detected **after RUNNING** may leave one or more committed local markers. This is deliberate fail-closed ambiguity: **the WRITE is UNKNOWN and must not be automatically retried**, even if the later audit or link is absent. The mock marker does not prove a real external operation, consent, delivery or exactly-once effects.

Focused regression: `tests/test_mock_cycle_durable_input_epoch_run391.py` (8 cases), including mutation before any durable write and mutation after RUNNING/reservation.

## 4. Validation contract and hard boundaries

The three packages add **25 regression cases**. They are intended to run under existing public-repository GitHub Actions with Ruff and pytest on Ubuntu/Windows, Python 3.11–3.13. The exact HEAD's CI result must be read from GitHub jobs and recorded in `docs/PROJECT_STATUS.md`, not inherited from a predecessor. Tests are local/synthetic; they do not use paid compute, external GPUs, paid APIs, new accounts/credentials, real capture, notifications, a physical PC, or live tool effects.

Additional limitations remain: private Python fields can be jointly forged by sufficiently privileged in-process code, caller time is untrusted, local hashes are not signatures, SQLite files have no cross-database atomicity, and a mock receipt cannot establish authenticated issuer approval, consent, external idempotency or exactly-once delivery. Do not promote a candidate, open protected V2 FINAL, change frozen contracts, merge PR #8 or PR #5, or activate any real WRITE based on these tests.

## 5. Next safe integration

After GREEN evidence at the exact source/test HEAD, audit restart recovery of a partially committed mock cycle using independently retained Planner/Occurrence/Audit witnesses. Separately advance Memory CAS/coherent snapshots and privacy lifecycle diagnostics. Keep the JARVIS foundation reversible and disconnected until genuine approval, clock, provenance and backend gates are satisfied.
