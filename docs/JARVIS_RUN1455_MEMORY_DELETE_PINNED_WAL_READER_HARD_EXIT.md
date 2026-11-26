# Run1455 — Memory delete COMMIT with a surviving WAL reader

**Parent:** Draft PR #636, branch `research/run1448-memory-delete-native-commit-hard-exit-20261126`.
**Exact parent work-basis HEAD:** `9f4af6e41ece8c54cf651636435525a7f45e08dc`.
**Child:** `research/run1455-memory-delete-wal-reader-native-commit-20261126`.

## Scenario

This test composes two already separate local SQLite boundaries:

1. A spawned writer calls the production `SQLiteMemoryStore.delete()` path. Its connection wrapper exits the process immediately after the native SQLite context manager returns from COMMIT, before `delete()` can perform post-COMMIT checks, close the handle, or return.
2. An independent read-only parent connection holds a pre-delete WAL snapshot throughout the writer's commit and process exit.

The pinned reader must continue to see the old row/event prefix. A TRUNCATE checkpoint must remain incomplete while that reader is open. After the reader closes, a cold store must recover the committed delete row/event pair, retain an unrelated row, reject the stale generation token, and complete a TRUNCATE checkpoint. Reopen verifies the same final state.

## Scope and evidence

Synthetic owner/namespace/content and a disposable local SQLite database only. No production Memory source, schema v1 DDL, event format, retention policy, public API, or frozen contract changes.

This is native-COMMIT process-exit plus a surviving-reader/last-close regression. It is **not** fsync/power-loss durability, physical erasure, independent custody, trusted time, authenticated consent, cross-store atomicity, or external exactly-once behavior. A stale-generation denial is local CAS evidence only.

No paid/external compute, credentials, hardware, Candidate, protected V2 evaluation, main write/merge, or UI/frontend work occurred. PR #8 remains Draft/unmerged; PR #636 remains Draft/unmerged. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no PASS is claimed.
