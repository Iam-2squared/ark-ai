# Run1167 — Memory WAL crash and delete/recreate ABA rebase

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent HEAD at child creation: `0ad2cc18229d810d1678c014aec4e904c8d81edc`.
- Rebased the test-only WAL/ABA regression from Draft PR #342 exact child HEAD `a6e84fcb305a57eff0449878ba615c6ed21e3e7c`.
- Source exact-head CI [45120422012](https://github.com/Iam-2squared/ark-ai/actions/runs/45120422012) was GREEN on the source head only; it does not transfer to this rebase.
- New branch: `research/run1167-memory-wal-aba-rebase`.

## Coverage

A spawned-process regression composes three local invariants:

1. A WAL reader pins the original row/event snapshot while a writer deletes and recreates the same deterministic Memory ID at revision 1.
2. The child reader exits without closing its SQLite transaction while a second independent reader remains alive; a TRUNCATE checkpoint remains busy/incomplete until the final reader closes.
3. After the last-close checkpoint and cold reopen, the original generation token remains rejected despite reuse of the same Memory ID and revision, while a freshly observed token can update the new lifetime.

The test covers read-only and read-write child readers, retained global event sequence, SQLite quick_check, stale-token denial without row/event mutation, and successful use of a fresh generation token.

## Evidence and limits

Test-only, using synthetic identifiers and disposable temporary SQLite files. This does not prove power-loss/fsync durability, authenticated writer provenance, trusted time, independent custody, physical erasure, cross-store atomicity, consent, or external-action authorization. No production Memory source/schema/API or frozen contract changes.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No paid/external compute, Candidate, protected V2 evaluation, credentials, hardware, UI/frontend work, destructive operation, or main merge. PR #5 and #8 remain Draft/unmerged; PR #9 remains untouched; ARK/JARVIS remains NOT_PASSED.
