# ARK AI Run864 — bounded SQLite diagnostics and catalog admission (non-UI)

**Observed:** 2026-11-14, Asia/Tokyo/JST. **ARK/JARVIS: NOT_PASSED.** The following work was saved only on `research/jarvis-foundations`, Draft PR #8. It is disconnected, reversible, free-only fixture hardening, NOT human approval, independently trusted time, real tool dispatch, or proof of exactly-once effects.

## Initial verified basis / prior exact-head evidence

- Initial work-basis HEAD `890aea2e2f1267ec7e9f4772a9d67eb521a916d7` (Run863 checkpoint), and `docs/PROJECT_STATUS.md` prior blob `1c74b8d2d2193494e19d8e108dda06b91fa2b263`.
- Verified [Actions #43558567669](https://github.com/Iam-2squared/ark-ai/actions/runs/43558567669): **6/6 GREEN** on this exact Run863 checkpoint HEAD (Ubuntu/Windows × Python 3.11/3.12/3.13), not on the Run864 changes.
- PR #5 and #9 initially verified Draft/open/unmerged. PR #9 Next Generation UI remains untouched and **all new UI work PAUSED**.
- Existing canonical V1/V2/Local UI/Launcher contracts, evaluated evidence and protected V2 final gate unchanged.

## NEW work — three independent, non-UI packages; 15 synthetic cases authored

1. **Atomic preaction SQLite catalog/quick-check**: `d538c0ee3eaee28e7cd88e33c8c51d5fd4cb96c0` source and `c39183b1d93b9442da93bd680d2208d2f0b2e3f2` regression. In `disconnected_atomic_preaction_ledger.py`, require one exact `('ok',)` quick-check diagnostic after at most two rows (`fetchmany(2)`), preflight catalog count exactly **4** (two tables + two SQLite autoindexes) and maximum SQL DDL bytes **4096** in the same transaction before Python DDL hydration. **Six synthetic regression cases**: four diagnostics outcomes, additional view and oversized schema with original count. No frozen DDL or real action authority changed.
2. **WRITE Slot Ledger SQLite catalog/quick-check**: `c9a05b5baa812422db58a5f3a6824384f4ee772e` source and `c153acb987c1513041f6e4ec4f1f200b2976e33d` regression. In `disconnected_write_slot_ledger.py`, preflight exactly **3** catalog objects (one table + two SQLite-generated UNIQUE indexes) and at most **4096** SQL DDL bytes, then compare against the original schema, accepting only one `('ok',)` quick-check diagnostic with two-row maximum hydration. **Five cases** covering valid/corrupt/extra diagnostics and extra/oversized schema before private DDL leaves SQLite. No reservation replay granted.
3. **Planner journal SQLite quick-check**: `6f9c34bbba4997f65a18173d2b54e56f8bd4a898` source and `625b62286871edd948e311012f8f8de8ae5d87a6` tests. Keep the existing SQL-side **2-object/4096-byte** catalog preflight and exact schema comparison; replace unbounded `quick_check.fetchall()` with at most two rows. **Four synthetic cases** cover single clean diagnostic, corruption, clean plus unexpected second diagnostic, and multiple corrupt diagnostics. Does not alter crash recovery, recovered RUNNING manual-only UNKNOWN or dependent-replay prohibitions.

**Total: 15 new regression cases AUTHORed, not an exact latest-head 6/6 PASS claim.** Tests use disposable `:memory:` connections, synthetic diagnostic cursors, and DDL-access sentinels forbidding Python hydration before SQL preflight. A separate local `sqlite3` DDL-shape sanity check confirmed synthetic atomic and WRITE object counts of 4 and 3 with added 5000-character identifier variants exceeding the 4096-byte ceiling. This isolated check is **not** full-repo pytest/Ruff. No local physical Windows/GGUF or model evaluation was done.

## CI pipeline / evidence at initial post-source-test snapshot

- [#43563397091](https://github.com/Iam-2squared/ark-ai/actions/runs/43563397091), final new source+test HEAD `625b6228`: **QUEUED**, six matrix jobs, when observed; no GREEN claim.
- [#43563300227](https://github.com/Iam-2squared/ark-ai/actions/runs/43563300227), atomic regression intermediate HEAD `c39183b1`: **IN PROGRESS**, six jobs, when observed.
- [#43563319674](https://github.com/Iam-2squared/ark-ai/actions/runs/43563319674), WRITE source `c9a05b5b`: **IN PROGRESS** when observed.
- Earlier intermediate HEADs produced automatic CI; no redundant equivalent workflow was manually dispatched. Future report/checkpoint commits may each trigger their own automatic runs, and must be checked against their **own exact HEAD**.

## Independent read-only risk audit

The existing disposable `scripts/diagnose_ark_store_wal_last_close.py` and `tests/test_ark_store_wal_last_close_run847.py` cover Memory/ActionAudit WAL last-client close with temporary databases, a child process, and a held SHM descriptor on supported POSIX systems. `UNLINKED` after final close is **not** a durable witness; SQLite may create a new sidecar on reopen. Neither last-close observations nor two matching sidecar inventories establish stable future pathname-to-open custody, independent COMMIT-UNKNOWN attribution, authenticated audit time, or external exactly-once effects. No such inference was made.

## Frozen boundaries and unresolved blockers

V1/V2/Local UI/Launcher frozen contracts/evidence unchanged. PR #5 and #9 Draft/unmerged; PR #8 Draft/unmerged. No new UI/frontend work, main merge, paid/external compute, Candidate training/promotion, protected evaluation, credential/account connection, personal data disclosure, user consent claim, real ToolBackend dispatch, or irreversible action.

**NOT_PASSED**: Memory/ActionAudit WAL/SHM last-close and path-to-open races, independent Memory COMMIT-UNKNOWN custody, multi-store atomicity, durable approval/occurrence integrity, trusted-clock audit-before-action and restart-safe external exactly-once effects. Bounded SQLite diagnostics address only finite Python result hydration and schema admission, not SQLite internal work or provenance.

## Next plan / 今後の方針

1. Verify Run864 exact-head six-job matrix and resulting report/checkpoint HEADs. On FAIL, inspect logs and repair only the failing semantics while preserving denial rules; use other independent non-UI lanes while CI runs.
2. Review SQL catalog preflight and SQLite quick-check cursor handling under both Windows and Ubuntu; keep frozen DDL untouched.
3. Probe disposable Memory/ActionAudit WAL/SHM final-close/name-open custody and independently attributable COMMIT-UNKNOWN without replaying unknown effects.
4. Preserve Planner UNKNOWN/manual-only quarantine, Memory coherent CAS/retention, privacy-safe Personal Context expiry/revocation, proactive scheduler and observation offline fixture contracts.
5. Connect ToolRegistry, exact-type PermissionGate, durable occurrence, trusted-clock audit-before-action and mock executor only after lower-level exact-head GREEN and never grant real execution authorization.
