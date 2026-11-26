# Run1458 — proactive-state native COMMIT with a surviving WAL reader

**Parent:** Draft PR #8, branch `research/jarvis-foundations`.
**Exact parent work-basis HEAD:** `6f78206e68b2c9b2799f77af29d51f6a4ddcca4c`.
**Child:** `research/run1458-proactive-state-pinned-wal-reader-hard-exit-20261126`.

## Scenario

The test initializes the existing synthetic proactive-state ledger, explicitly enables SQLite WAL mode, and pins an independent read-only snapshot of the empty state table. A spawned writer constructs the production ledger, performs one synthetic `evaluate()` transition, and exits immediately after native SQLite `Connection.commit()` returns—before the state receipt or Python cleanup.

The pinned reader must continue to see the empty prefix. A TRUNCATE checkpoint must remain incomplete while that reader is open. After the last reader closes, cold reconstruction must expose exactly one revision-1 `ELIGIBLE_PREVIEW` state with the original observation digest and rolling-window fields. A stale genesis CAS retry must conflict and leave the single committed state unchanged.

The test also requires schema version 1, SQLite `quick_check`, successful final TRUNCATE checkpoint, and absence of the synthetic raw observation marker from persisted database/WAL/SHM files.

## Scope and evidence limits

Test-only synthetic local SQLite evidence. No proactive ledger source, DDL/schema, policy vocabulary, CAS semantics, public API, scheduler activation, timer, notification, or frozen contract changes.

This composes native-COMMIT process-exit with a surviving WAL reader and last-reader checkpoint behavior. It is **not** fsync/power-loss durability, independent custody, trusted time, authenticated consent, notification permission, scheduler execution, external dispatch, automatic replay, cross-store atomicity, or exactly-once external effects. `ELIGIBLE_PREVIEW` remains a local scheduling decision only.

No paid/external compute, credentials, hardware, Candidate, protected V2 evaluation, main write/merge, or UI/frontend work occurred. PR #8 remains Draft/unmerged. Fresh exact-head CI is required; no PASS is claimed.
