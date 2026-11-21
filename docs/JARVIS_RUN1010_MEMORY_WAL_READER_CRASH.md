# Run1010 — Crashed final pinned Memory WAL reader

**Work basis:** Draft PR #8 exact head `ce4b567605896fe1bda4fa8458fe448701b9dced`. This is an isolated test-only child; it does not modify PR #8, Memory source, the frozen Memory v1 schema/API, or another child branch.

## Regression

A spawned process opens a pinned SQLite WAL read transaction over one synthetic Memory row and its event prefix. An independent managed Memory writer commits revision 2 and the matching update event while that reader remains alive. The child verifies its historical revision-1 snapshot, then terminates through `os._exit(0)` without rollback or connection close.

The parent requires:

- the child exits successfully after the writer commit;
- a fresh managed Memory store recovers the committed row/event pair;
- `PRAGMA wal_checkpoint(TRUNCATE)` reports no busy reader and all log frames checkpointed;
- SQLite `quick_check` remains `ok`;
- replay of the pre-write generation token is rejected; and
- a second cold reopen returns the same revision-2 row and two-event history.

The test runs with both a read-only URI connection and a normal read/write SQLite connection. It specifically exercises the final reader process dying while it owns the WAL snapshot; the existing Run1003 regression separately covers a crashed reader while another independent reader remains pinned.

## Safety and limitations

Only disposable local SQLite, spawned processes and synthetic Memory values are used. No production source, schema, public contract, live personal data, external service, tool dispatch, notification, model, paid compute, Candidate, protected V2 evaluation or main branch is changed.

This exercises process-death lock release and local WAL recovery after a committed write. It does **not** prove power-loss durability, storage-device flush behavior, authenticated writers, anti-rollback, independent custody, trusted time, consent, or external-effect delivery. A SQLite generation token remains local CAS evidence only.

**Validation:** authored test and report; exact-head CI is pending. No PASS is claimed. PR #8 remains Draft/unmerged. Overall ARK/JARVIS remains NOT_PASSED.
