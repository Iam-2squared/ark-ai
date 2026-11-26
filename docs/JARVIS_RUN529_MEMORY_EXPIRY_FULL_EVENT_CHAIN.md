# Run529 — SQLite Memory expiry preview, complete bounded row/event lifecycle

**Free-only, disconnected, read-only diagnostic.** No deletion, trusted clock, owner authentication, personal content disclosure, automatic replay, or backend execution.

## Why the earlier last-event check was incomplete

A live due row can have a final `update` event whose revision matches the row while a preceding `create` or intermediate `update` has been removed or forged. A same-revision final event alone cannot establish an internally coherent local event chain. Likewise, a forged stored event timestamp can preserve all other final-event identifiers. The existing preview already uses a read transaction and verifies `limit+1` rows; this change preserves both properties.

## Implementation

- `src/ark/memory/expiry_candidate_preview.py`: `_check_due_event_chain` reconstructs the event lifecycle for every candidate, including the overflow pagination row, **inside the existing read-only SQLite transaction**.
- Requires exact event ID, owner/namespace, operation, integer revision and timestamp. The active cycle starts at `create/revision=1`, advances one revision per `update`, and any terminal `delete` or `expire` closes the cycle. A later `create/revision=1` is legitimate after deletion and is explicitly supported.
- Requires the final live event revision to equal the row revision, its time to equal `updated_at_ms`, and the active cycle's creation time to equal `created_at_ms`. Absent, skipped, forged, out-of-scope, out-of-order or terminal-only histories are rejected. Total scanned events are bounded across **all** selected and overflow rows to 40,000; exceeding the cap rejects rather than partially accepting history.
- These are local SQLite consistency checks, **not signed historical authorship**, a deletion authorization, or a lock spanning a later purge. The existing verify path can rescan the same requested page but does not grant future TOCTOU-free action.

## Tests and exact-head CI

- New `tests/test_memory_expiry_full_lifecycle_run529.py`: **9 authored pytest cases**, including missing update in a three-revision chain, forged first revision, early terminal, forged event/create timestamps, mid-chain scope retarget, malformed overflow-row history, valid delete/recreate cycle, and normal updated-page pagination.
- Source HEAD `174e8f513e60b61d9c821ff154c982206ca39eaf`; source+test HEAD `3487049ba2887c6c5dd1ca2595ee99ecdb4cf9c7`.
- Exact-head [GitHub Actions CI 41305225866](https://github.com/Iam-2squared/ark-ai/actions/runs/41305225866): **5/6 GREEN, 1 IN PROGRESS (Windows Python 3.12) at this documentation write**. No final six-job PASS claim until its last job completes successfully.
- The authored test count is not independent local pytest evidence: git checkout cannot resolve GitHub DNS here. Later documentation/checkpoint commits need their own exact-head CI.

## Boundaries and next directions

Memory schema v1 remains frozen. New checks do not change `SQLiteMemoryStore.purge_expired()`, trigger erasure or infer consent. Continue CAS/concurrent writer/restart evidence with retained independent witnesses; couple no real external action until Planner, registry, permission, audit and persistence gates have proven exact-head GREEN.
