# Run1024 — Memory logical expiry and local-clock rollback boundary

## Exact work basis

- Parent workstream: Draft PR #8, `research/jarvis-foundations`.
- Parent HEAD at branch creation: `ca480e5d84a011fc86978aae33db20e0a5538649`.
- This package is a test and contract-clarification only. It does not change Memory v1 DDL, public APIs, clock behavior, or production code.

## Verified behavior

`SQLiteMemoryStore.get()` and `search()` apply the injected local clock as a per-read logical expiry filter. The base Memory clock contract accepts a valid non-negative integer but does not require monotonicity. Therefore, when a record has not been explicitly purged, a clock observation at or beyond `expires_at_ms` can hide the record and a later lower clock observation can make the same row visible again.

`include_expired=True` is a diagnostic read path that skips expiry-clock sampling and does not mutate the event log. `purge_expired()` is a separate explicit SQLite write transaction: it deletes selected rows and appends corresponding `expire` events in the same database transaction. The test verifies that an explicitly purged row remains absent after a later local clock rollback.

## Added regression coverage

`tests/test_memory_expiry_clock_rollback_boundary_run1024.py` uses synthetic identifiers, synthetic content, a disposable SQLite database, and an injected clock to pin:

1. logical expiry visibility may reverse after local clock rollback while the row remains present;
2. `include_expired=True` does not sample the local clock;
3. read-only expiry filtering does not append events; and
4. explicit purge removes the row and records one expiry event that is not reversed by a later clock rollback.

## Interpretation and hard limits

This is a deliberately narrow compatibility statement, not a recommendation to rely on clock rollback. The injected clock is not authenticated or independently trusted. The test does **not** establish trusted time, consent, retention authorization, privacy erasure, secure deletion, backup removal, independent writer identity, power-loss durability, or cross-store atomicity.

Memory v1 schema and API remain frozen. No durable expiry high-water is introduced. A separate high-water design would need to resolve at least:

- whether a forward wall-clock jump may permanently advance expiry;
- how a high-water update is ordered against row/event purge and how ambiguous COMMIT outcomes recover;
- how concurrent processes share one authoritative frontier without adding an unreviewed Memory v1 table or changing its exact DDL;
- how restart and sidecar-loss cases fail closed without silently recreating state; and
- which retention policy and time authority authorize irreversible deletion.

A sidecar ledger cannot be treated as transactionally atomic with the existing Memory database merely because both use SQLite. A max-seen wall clock is not a trusted clock and can turn a false forward jump into premature deletion. No implementation or policy decision is made here.

## Validation boundary

Exact-head Windows/Linux CI is required before this package can be treated as validated. No local pytest/Ruff PASS is claimed. All work remains isolated under a Draft child PR of #8; PR #5 remains gated Draft/unmerged, PR #9 remains paused and untouched, and main is not changed.
