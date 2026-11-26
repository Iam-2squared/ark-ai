# Run1001 — Crashed pinned WAL reader and last-lock recovery

**Work basis:** Draft PR #8 exact head `0049080e49a5a83e0cb5a439a0ad2924389b910f`. This is an isolated test-only child branch; it does not modify PR #8, Memory source, the frozen Memory v1 schema/API, or any existing child PR.

## Regression

A spawned process opens a pinned SQLite WAL read transaction over one synthetic Memory row and its event prefix. An independent managed Memory writer then commits revision 2 and its matching update event while that reader remains alive. The child verifies that its historical snapshot is still revision 1, then terminates via `os._exit(0)` without rollback or connection close.

The parent requires:

- the child exits successfully after the writer commit;
- a fresh managed Memory store recovers the committed row/event pair;
- `PRAGMA wal_checkpoint(TRUNCATE)` reports no busy reader and all log frames checkpointed;
- SQLite `quick_check` remains `ok`;
- replay of the pre-write generation token is rejected; and
- a second cold reopen returns the same revision-2 row and two-event history.

The test runs with both a read-only URI connection and a normal read/write SQLite connection.

## Safety and limitations

Only disposable local SQLite, spawned processes and synthetic Memory values are used. No production source, schema, public contract, live personal data, external service, tool dispatch, notification, model, paid compute, Candidate, protected V2 evaluation or main branch is changed.

This exercises process-death lock release and local WAL recovery after a committed write. It does **not** prove power-loss durability, storage-device flush behavior, authenticated writers, anti-rollback, independent custody, trusted time, consent, or external-effect delivery. A SQLite generation token remains local CAS evidence only.

**Validation:** test and report are authored; exact-head CI is pending. No PASS is claimed. PR #8 remains Draft/unmerged. Overall ARK/JARVIS remains NOT_PASSED.
