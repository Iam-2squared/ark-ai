# Run1174 — Run1174: Memory WAL reader crash cannot erase a delete/recreate ABA fence

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent HEAD at branch creation: `107b56849fec47e4d2e24576958b358c0aef697b`.
- Rebased the test-only package from Draft PR #352 exact child HEAD `2946be120c061cd12b035b5b00aa9dc859b7e2c7`.
- Source package: Draft PR #342 exact head `a6e84fcb305a57eff0449878ba615c6ed21e3e7c`.
- Source exact-head CI [45141766193](https://github.com/Iam-2squared/ark-ai/actions/runs/45141766193) was GREEN on the prior child head only; it does not transfer to this rebase.
- New branch: `research/run1174-memory-wal-aba-rebase`.

## Coverage

A spawned-process regression composes three local invariants: (1) a WAL reader pins the original row/event snapshot while a writer deletes and recreates the same deterministic Memory ID at revision 1; (2) the child reader exits without closing its SQLite transaction while an independent keeper remains alive, so a TRUNCATE checkpoint remains incomplete until the final reader closes; and (3) after last-close checkpoint and cold reopen, the original generation token remains rejected despite ID/revision reuse, while a fresh generation token can update the new lifetime. Read-only and read-write child readers, retained global event sequence, SQLite quick_check, stale-token denial without row/event mutation, and successful fresh-token update are covered.

## Evidence boundary

Test-only, using synthetic identifiers and disposable temporary SQLite files. This does not prove power-loss/fsync durability, authenticated writer provenance, trusted time, independent custody, physical erasure, cross-store atomicity, consent, or external-action authorization. No production Memory source/schema/API or frozen contract changes.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No paid/external compute, Candidate generation/promotion, protected V2 evaluation, credentials, hardware, UI/frontend work, frozen-contract change, destructive operation, or main merge. PR #5 and #8 remain Draft/unmerged; PR #9 remains untouched; ARK/JARVIS remains NOT_PASSED.
