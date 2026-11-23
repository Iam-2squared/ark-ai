# Run1216 — Memory WAL delete/recreate ABA crash regression on current foundation

## Exact basis

- Repository: `Iam-2squared/ark-ai`.
- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `15d983ded8efe7df0b80e1d5c0b1e44d4c8caf93`.
- Rebased test-only source: Draft PR #398, `research/run1214-memory-wal-aba-latest`, exact child HEAD `6464d933044d33673d0a4eddd6966287be6be835`.
- Source predecessor exact-head CI [45242685693](https://github.com/Iam-2squared/ark-ai/actions/runs/45242685693) was GREEN 6/6 on its predecessor child only; it does not transfer to this rebase.
- New child branch: `research/run1216-memory-wal-aba-crash-rebase`.

## Coverage

The spawned-process regression composes three local invariants:

1. A WAL reader pins the original row/event snapshot while a writer deletes and recreates the same deterministic Memory ID at revision 1.
2. The child reader exits without closing its SQLite transaction while an independent keeper remains alive, so a TRUNCATE checkpoint remains incomplete until the final reader closes.
3. After last-close checkpoint and cold reopen, the original generation token remains rejected despite ID/revision reuse, while a fresh generation token can update the new lifetime.

Both read-only and read-write child readers are exercised. The test checks the retained global event sequence, SQLite `quick_check`, stale-token denial without row/event mutation, and successful fresh-token update.

## Compatibility

The package is test-only. It uses the existing public generation-CAS entrypoints and does not modify Memory production source, schema, public API or frozen contracts. The parent now also contains the Planner durable journal package; no Planner files are changed here.

## Evidence boundary

Synthetic identifiers and disposable temporary SQLite files only. This does not prove power-loss/fsync durability, authenticated writer provenance, trusted time, independent custody, physical erasure, cross-store atomicity, consent, or external-action authorization. The generation token is a local CAS witness, not consent or dispatch authority.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed. No paid/external compute, Candidate generation/promotion, protected V2 evaluation, credentials, hardware, UI/frontend work, frozen-contract change, destructive operation, or main merge. PR #5/#8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
