# Run1157 — Memory WAL crash and delete/recreate ABA rebase

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `9b1dbc439ec338e2840d9dc493e724c651617e60`.
- Rebased from Draft PR #63 exact child HEAD: `ce85bd2719a84cf8547fcd000ad9827060fb9f6c`.
- Source exact-head CI: [44707049154](https://github.com/Iam-2squared/ark-ai/actions/runs/44707049154) GREEN, 6/6 on the source head only; it does not transfer to this rebase.
- New child branch: `research/run1157-memory-wal-aba-rebase-latest`.
- Test: `tests/test_memory_wal_crash_delete_recreate_aba_run1017.py`.

## Coverage

The spawned-process regression composes three local invariants:

1. A WAL reader pins the original row/event snapshot while the writer deletes and recreates the same deterministic Memory ID at revision 1.
2. The child reader exits without closing its SQLite transaction while a second independent reader remains alive; a TRUNCATE checkpoint must remain busy/incomplete until the final reader closes.
3. After last-close checkpoint and cold reopen, the original generation token remains rejected despite the reused memory ID and revision, while a freshly observed token can update the new lifetime.

The test is parameterized for read-only and read-write child readers. It checks the retained global event sequence, final SQLite quick_check, stale-token denial without row/event mutation, and successful use of a fresh generation token.

## Evidence and limits

Test-only, using synthetic identifiers and disposable temporary SQLite files. This does not prove power-loss/fsync durability, authenticated writer provenance, trusted time, independent custody, physical erasure, cross-store atomicity, consent, or external-action authorization. No production Memory source/schema/API or frozen contract changes.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no PASS is claimed before that run completes. No live personal data, real backend, paid service, external compute, credentials, Candidate, protected V2 evaluation, UI/frontend work, or main merge is included. PR #5 and #8 remain Draft/unmerged; PR #9 remains untouched; ARK/JARVIS remains NOT_PASSED.
