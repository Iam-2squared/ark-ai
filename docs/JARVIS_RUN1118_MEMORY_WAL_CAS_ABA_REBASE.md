# ARK AI Run1118 — Memory cross-process WAL CAS and delete/recreate ABA

**Exact work basis:** Draft PR #8 branch `research/jarvis-foundations`, commit `a5e961876eb24adba97573bb34228740c1344d9e` (the isolated merge of PR #296).  
**Child branch:** `research/run1118-memory-wal-cas-aba-rebase`.  
**Scope:** test-only reapplication of the older Run993 cross-process WAL/CAS regression (PR #17) and Run1017 WAL crash/delete-recreate ABA regression (PR #63). No production source, schema, public API or frozen contract is changed.

## Coverage

1. **Pinned WAL snapshot with competing cross-process CAS writers**
   - Spawn one read-only process that pins the original row/event snapshot.
   - Spawn two independent writers with the same retained generation token.
   - Require exactly one revision-2 update and one CAS conflict.
   - Keep the pinned reader on the original row/event prefix until rollback; then require it to see the committed update.
   - Reject replay of the retained pre-write token and verify SQLite `quick_check`.

2. **WAL reader hard-exit across delete/recreate ABA**
   - Parameterize a spawned read-only and read-write reader.
   - Keep a second independent reader alive while the writer deletes and recreates the same deterministic Memory ID at revision 1.
   - Hard-exit the child with its read transaction still open; require the keeper to preserve the old snapshot and a TRUNCATE checkpoint to remain incomplete.
   - After last-close checkpoint and cold reopen, reject the stale generation token despite reused ID/revision; accept only a newly observed token.
   - Verify the exact create/delete/create/update event sequence and final SQLite `quick_check`.

## Evidence boundary

These are disposable local SQLite fixtures with synthetic owner, namespace, source and content values. They exercise SQLite WAL/CAS behavior across spawned processes; they do not establish power-loss/fsync durability, authenticated writer provenance, independent custody, trusted time, consent, physical erasure, cross-store atomicity, or external-action authorization. Generation tokens remain local CAS witnesses and never authorize a tool action.

## Validation

The two suites contain one ordinary test plus a two-mode parameterized test (three cases total). They have been rebased onto the exact Run1117 parent commit above. **Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no PASS is claimed at authoring time.** CI on the older PR #17/#63 bases does not transfer to this branch.

PR #8 remains Draft/unmerged; PR #5 remains gated Draft/unmerged; PR #9 remains untouched and UI remains paused. No paid/external compute, Candidate generation/promotion, protected V2 evaluation, credentials, physical hardware action, destructive operation or main merge is included. **ARK/JARVIS remains NOT_PASSED.**
