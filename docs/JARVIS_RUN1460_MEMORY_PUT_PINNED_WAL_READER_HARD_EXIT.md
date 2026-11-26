# Run1460 — Memory put row/event COMMIT with a surviving WAL reader

**Parent:** Draft PR #8, branch `research/jarvis-foundations`.
**Exact parent work-basis HEAD:** `7e3cbc3fc838599778485c89811e3efd8fba6f0c`.
**Child:** `research/run1460-memory-put-pinned-wal-reader-hard-exit-20261126`.

## Scenario

The test creates one synthetic Memory row and its revision-1 `create` event through the production `SQLiteMemoryStore.put()` API. An independent read-only connection then pins the pre-update WAL snapshot. A spawned writer updates the same row through the production API and exits immediately after native SQLite COMMIT returns, before the caller receives its MemoryRecord or post-COMMIT checks can run.

The pinned reader must retain the old content, revision 1 and create-event prefix. TRUNCATE checkpoint must remain incomplete while the reader is open. After last-reader close, cold readback must expose the new content at revision 2 and exactly one matching `update` event. A stale revision-1 CAS retry must conflict without adding another event. Final checks require the frozen Memory v1 schema/event columns, schema version 1, quick_check, and a successful TRUNCATE checkpoint.

## Scope and evidence limits

Test-only synthetic local SQLite evidence. No Memory source, v1 DDL/schema, event format, retention policy, public API, or frozen contract changes.

This composes production `put()` row/event atomicity with native-COMMIT process exit and a surviving WAL reader. It does **not** prove fsync/power-loss durability, independent custody, authenticated writer provenance, trusted time, consent, physical erasure, cross-store atomicity, or exactly-once external effects. The stale-CAS conflict is local revision evidence only; no automatic retry is added.

No paid/external compute, credentials, hardware, Candidate, protected V2 evaluation, main write/merge, or UI/frontend work occurred. PR #8 remains Draft/unmerged. Fresh exact-head CI is required; no PASS is claimed.
