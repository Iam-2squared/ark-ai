# Run489 — Disconnected due restart, Memory witness carrier custody, privacy authority fence, V3 lineage types

**Work:** 2026-10-31 JST; **source branches:** Draft PR #8 `research/jarvis-foundations` and Draft PR #5 `research/v3-learning-evaluation`. This is provisional implementation/evidence only, **ARK overall NOT_PASSED**. No external hardware, GPU, paid services, real-world Tool action, protected V2 opening, Candidate creation, automatic promotion or main merge.

## Work basis and saved heads

- Run488 starting PR #8 HEAD `480a7112742098df959a43c1fb3b36153ff24e6e`; source work started from that exact HEAD, PR #8 final code/test HEAD before this document: `af8c5aef6bc6be1b338f2e6dff34e3575d135970`.
- Run488 starting PR #5 HEAD `79376f3ce777dc877c63ce58785153e493b9b7fc`; PR #5 final code/test HEAD: `b754608f41e9848ed7c8755aa46608d1af056910`.
- All branch edits used the regular GitHub Contents API, re-reading latest refs before each write. No forced ref manipulation, merge or irreversible operation. Concurrent new branch heads must be re-verified before downstream action.

## NEW work: four independent source/test packages (64 pytest parameter cases)

1. **Scheduler due ledger — existing-only recovery (17 new cases)**. `src/ark/agency/disconnected_due_reservation.py` blob `05874bee7a1fc34b0f0d75984d332e2f1fd3b43d`; `tests/test_due_restart_retained_existing_run489.py` blob `2d37f86c6533ecb1f8f003f1b4857d4b8c257c93`. New opt-in `require_existing=True` mode uses an existing SQLite file rather than silently creating one; `reopen_with_witness(...,retained=...)` rechecks a separately retained exact tip and refuses a missing database, old tip, uninitialized file or invalid type. Legacy fixture creation without the option remains supported. The constructor still acquires a SQLite write-intent lock even when only verifying existing storage, so this is **not** a truly read-only bootstrap; no external action is executed or authorized. Path/SQLite races remain best-effort.
2. **Memory witness ledger — exact carrier pinning (6 new cases)**. `src/ark/memory/disconnected_witness_ledger.py` blob `38f1ca213f30cc9111bb7c6beaa9c8790d68c60c`; `tests/test_memory_witness_source_custody_run489.py` blob `7b9de3a086352decb8f6d02c0e990a39de0991ed`. Inspect now pins the original Path identity and retained witness fields across open, transaction, validation and commit; append also rejects a rebound equal-valued ledger Path. This rejects reentrant reflective fixture mutation; it does **not** establish independent writer identity or protect against arbitrary OS-level path replacement.
3. **Personal Context retention — inert result authority (6 new cases)**. `src/ark/personal_context_retention_recheck_review.py` blob `c95e20784380127ec9838a054262a6c57a9335c0`; `tests/test_retention_recheck_authority_fence_run489.py` blob `27e0b2051b1e891b3fe516f35ad611b3771cdc22`. Captures original diagnostic result type and rejects re-bound constructors or properties claiming deletion permission, erasure completion, context use or external disclosure. No actual erasure/consent/disclosure proven.
4. **V3 lineage — exact identity carriers (35 new cases)**. `src/ark/learning/lineage.py` blob `5cc1e3582f7c730c1f9526d8ee903f1b9f438c26`; `tests/v3/test_lineage_exact_carriers_run489.py` final blob `ad2031c9204d45cd8f9863df8b71175f12eebb55`. Reject non-exact strings, invalid/control payloads, non-exact SHA256, bool/float byte sizes, bool schema version, quantization subclasses and forged artifact identity objects before generating canonical lineage bytes. Does not load model files or start training.

## Verification and CI at evidence composition

- Run #1722 / [workflow 41140350170](https://github.com/Iam-2squared/ark-ai/actions/runs/41140350170), HEAD `b754608f41e9848ed7c8755aa46608d1af056910`: **queued**.
- Run #1721 / [workflow 41140289600](https://github.com/Iam-2squared/ark-ai/actions/runs/41140289600), HEAD `af8c5aef6bc6be1b338f2e6dff34e3575d135970`: **queued**.
- Run #1719 / [workflow 41140205826](https://github.com/Iam-2squared/ark-ai/actions/runs/41140205826), HEAD `792e54bccb9ba3d7d06c43ce7800e4f1a47a79d4`: **in_progress**.
- Run #1717 / [workflow 41140128403](https://github.com/Iam-2squared/ark-ai/actions/runs/41140128403), HEAD `27f9b45d258c38d7e2ca3c2af4dcc8a8884f431e`: **completed / failure**.
- PR #5 intermediary #1717 / `41140128403` **FAIL (six environments)**: source implementation was GREEN at #1716, but new test accidentally exercised the literal `\\x00` text rather than an actual NUL control character. Ubuntu Python 3.12 log: `1 failed, 619 passed`, with the one failure `test_artifact_text_fields_require_exact_inert_strings[path-local\\x00binary]`. Test repaired by using `"local" + chr(0) + "binary"` without altering the security implementation; latest V3 HEAD must be checked independently. No test was removed.
- Independent local full `pytest` and `ruff` **NOT VERIFIED** (local `github.com` DNS fetch unavailable). Source and tests are saved; **latest HEADs are not GREEN solely because old CI passed**.
- Frozen Memory v1 contract `b6e93821ecd69270a7634aceb20775dc36e9953c`, Agency contract `13f1bb725f9c2c783e29402ca4a6e0f86b850ef9` unchanged. No frozen V1/V2/Local UI/Launcher evidence or V3 Contract 1 changed.

## Limitations and next plan

1. Resolve **exact final-head** CI on both PRs; diagnose only actual FAIL jobs and preserve safety semantics, rerun only after fixes.
2. Keep all Draft PRs unmerged. Improve existing-only due open path to use a true read-only SQLite transaction without relaxing other constructor migration rules.
3. Continue manual UNKNOWN WRITE reconciliation (never auto-retry), durable Memory CAS/path identity and SQLite witness loss safeguards.
4. Advance Trusted Clock audit-before-action and one-shot authorization with disconnected/mock-only executor; enforce approval and privacy lifecycle independently.
5. Maintain zero-cost-only V3 reproducibility and approval packet guards; never open paid training, Candidate generation, protected V2, external GPU or promotion without explicit separate human gate.

**Saved at observation for this document:** 2026-10-31T07:47:09+09:00 Asia/Tokyo/JST; local timestamp is NOT authenticated time or approval.
