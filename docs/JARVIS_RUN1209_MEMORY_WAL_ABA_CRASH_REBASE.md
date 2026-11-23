# Run1209 — Memory WAL delete/recreate ABA crash regression on latest foundation

## Exact basis

- Repository: `Iam-2squared/ark-ai`.
- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent work-basis HEAD at branch creation: `5059b08222c309c173c17dcb8e246dd9599be7a4`.
- Rebased test-only package from Draft PR #358 exact child HEAD: `1b80168de66770021f3640cd8c80fefbf4b30f09`.
- Earlier source PR #342 exact head: `a6e84fcb305a57eff0449878ba615c6ed21e3e7c`.
- Prior exact-head CI [45150850994](https://github.com/Iam-2squared/ark-ai/actions/runs/45150850994) was GREEN on PR #358's child head only; it does not transfer to this rebase.
- New child branch: `research/run1209-memory-wal-aba-crash-latest`.

## Coverage

The spawned-process regression composes three local invariants:

1. A WAL reader pins the original row/event snapshot while a writer deletes and recreates the same deterministic Memory ID at revision 1.
2. The child reader exits without closing its SQLite transaction while an independent keeper remains alive, so a TRUNCATE checkpoint remains incomplete until the final reader closes.
3. After last-close checkpoint and cold reopen, the original generation token remains rejected despite ID/revision reuse, while a fresh generation token can update the new lifetime.

Both read-only and read-write child readers are exercised. The test also checks the retained global event sequence, SQLite `quick_check`, stale-token denial without row/event mutation, and successful fresh-token update.

## Compatibility review

- `src/ark/memory/sqlite_store.py` is byte-identical to the earlier parent (blob `ca9196aec12204ee519e52c41f3a1674825499d7`).
- The latest parent has additional Unicode format-control admission in `src/ark/memory/generation_fenced_cas.py` (blob `437aa595d6daee14e3649d832a19e66b8c6c1ce9`). The regression uses ordinary ASCII scope/source identifiers and exercises the existing public generation-CAS entrypoints; it does not weaken or bypass that admission.
- No production Memory source, schema, public API or frozen contract is changed by this child.

## Evidence boundary

Synthetic identifiers and disposable temporary SQLite files only. This does not prove power-loss/fsync durability, authenticated writer provenance, trusted time, independent custody, physical erasure, cross-store atomicity, consent, or external-action authorization. The generation token is a local CAS witness, not consent or dispatch authority.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed. No paid/external compute, Candidate generation/promotion, protected V2 evaluation, credentials, hardware, UI/frontend work, frozen-contract change, destructive operation, or main merge. PR #5/#8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
