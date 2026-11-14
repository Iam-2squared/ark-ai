# Run657 — Audit-link receipt pre-access custody, Memory WAL triage, Planner recovery fence

**Scope:** Draft PR #8 (`research/jarvis-foundations`), local-first, disconnected and reversible **non-UI** core only. Initial verified PR HEAD: `07c7570055d06f1838150198b562c30496144a27` (Run656). Source/test basis was checked against the actual PR HEAD before each ordinary GitHub Contents API write. Administrative drafting time: 2026-11-06T17:50:15.359+09:00; **not** a trusted action clock.

## Package A — Pre-COMMIT synthetic audit-link receipt custody

**Production source:** `src/ark/agency/synthetic_occurrence_audit_link_review.py` commit `eb899335097d0f82ca1f56423e8aed46e58338ed`.

The local `SyntheticAuditLinkReceipt` previously tested the output type and fields *after* a SQLite link COMMIT. A replaced exported receipt factory or slotted field/getter could execute arbitrary local Python during post-COMMIT result construction. The new `_require_original_receipt_contract()` pins import-original **exact class identity**, three data field descriptors, constructor/allocation/attribute-lookup hooks and three deny-only authority properties. It rejects reflection-based changes before `link_synthetic` input inspection, during all original `assert_input_epoch()` reentrant checks, and before/after constructing the result through the import-pinned class. This is defense-in-depth within a local Python process; it is **not** sandboxing, user identity attestation, or an external exactly-once guarantee.

**Updated legacy tests:** commit `8385b73cba7c9250a098a05c93bf8542dc593051` updates **five existing parameterized cases**: a *preinstalled* replacement factory must never run, and the sidecar must remain unchanged, rather than expecting a previously allowed after-COMMIT error. Separate existing `test_committed_link_stays_durable_if_commit_callback_changes_source` still checks the important opposite boundary: if a callback changes source identity **after COMMIT**, denial must **not** pretend to roll back a committed link.

**New tests:** `tests/test_audit_link_receipt_preaccess_run657.py` commit `0200616561b36f5eb749370bf37e532124adb91a`, **12 authored cases**: nine preinstalled class-field/hook poison cases, two mutation injections at pre-action audit and link-hash callback phases (both rejected with no link insertion), and an unchanged deny-only successful receipt. The malicious callback is asserted uncalled. No inherited `__new__` slot is poisoned inside shared pytest; that allocation-hook safety principle follows Run651's CI repair.

## Package B — Memory COMMIT-UNKNOWN manual triage coherence

**New tests:** `tests/test_memory_triage_wal_post_snapshot_run657.py` commit `f373030eca7d2a9fde3e2cf4a4e0e33af87535fe`, **3 authored cases**. Two independent `SQLiteMemoryStore` handles on a disposable WAL database: the writer commits (a) matching UPDATE, (b) nonmatching content UPDATE, or (c) DELETE then RECREATE during the reader's `_row_hash` callback **after the old row snapshot and before the event scan**. The original read-only triage must observe the coherent prewrite image. The next fresh observation must distinguish a matching visible update (without actor attribution) from indeterminate changes. Neither result permits automatic retry, new WRITE authorization or consent inference. Production Memory code and frozen Memory v1 schema untouched.

## Package C — Planner journal → disconnected recovery policy boundary

**New tests:** `tests/test_planner_disconnected_recovery_fence_bridge_run657.py` commit `fbf8c09544506e0b9a8389bc86a95dc9c06e12df`, **5 authored cases**. Reopen the durable SQLite synthetic Plan journal with (a) ambiguous RUNNING WRITE, (b) FAILED WRITE, (c) CANCELLED WRITE, (d) synthetically SUCCEEDED WRITE, and (e) reserved-but-PENDING WRITE. A manual, explicitly **untrusted** transformation into detached `OfflineRecoveryStepClaim` values must classify unknown WRITE as quarantine, failed/cancelled descendants as terminal, pending reservation as quarantine, and an unrelated READ as mock-only ready. Even a synthetic `SUCCEEDED` remains `COMPLETE_UNVERIFIED`, never evidence of external outcome. No automatic backend integration or replay is introduced.

## Exact change boundary and CI custody

`07c75700...fbf8c095` via GitHub compare: **five fast-forward commits; exactly five changed paths** (one synthetic non-UI source, one existing test, three new test files). No `main`, PR #5, PR #9, frontend, frozen contract/evaluation or UI branch path changed. **20 new authored parameterized tests** (12 + 3 + 5), plus correction of five existing cases. This is **not** a claim of 20 measured passes. No local full-suite pytest/target-PC GGUF run is claimed, and the public clone in this execution environment still fails DNS resolution.

- Prior exact-head Run656: [CI #42184948241](https://github.com/Iam-2squared/ark-ai/actions/runs/42184948241), six matrix jobs **GREEN**.
- New source: [#42189516707](https://github.com/Iam-2squared/ark-ai/actions/runs/42189516707).
- Existing assertion update: [#42189631291](https://github.com/Iam-2squared/ark-ai/actions/runs/42189631291).
- Audit receipt regressions: [#42189740247](https://github.com/Iam-2squared/ark-ai/actions/runs/42189740247); Ubuntu 3/3 GREEN while Windows 3 jobs were in progress at first read.
- Memory WAL triage: [#42189987283](https://github.com/Iam-2squared/ark-ai/actions/runs/42189987283); Ubuntu 3.11 and 3.13 GREEN at first read, others still in progress.
- Planner recovery bridge: [#42190232799](https://github.com/Iam-2squared/ark-ai/actions/runs/42190232799); all six jobs in progress at first read.
- **Final exact-head six-job GREEN NOT YET VERIFIED at document drafting.** Later check the actual jobs and fix actual failures narrowly, using only the normal permitted source/test write API. Do not claim the source/test tree GREEN merely because intermediate jobs are green.

## Hard stops, architectural limitations and next priority

- PR #5 V3 Candidate/training and protected V2 final evaluation remain gated by explicit approval, pinned immutable identities and reviewed rights/cost controls. No paid service/external GPU, Candidate weights, model promotion, physical PC, secrets, real tool dispatch, notification, media capture, destructive action, main merge or unapproved frozen-contract change.
- PR #9 UI remains Draft/unmerged and **fully untouched**; all frontend work stays paused.
- The audit sidecar, source reservation database and action audit are **three separate SQLite transactions**. A locally matching link is not atomic across all stores or proof of live exactly-once dispatch. Both a missing link and a link surviving a post-COMMIT error remain manual-reconciliation cases.
- Prioritize exact-head CI completion; next address Memory COMMIT-UNKNOWN row/event lineage under two writers, Planner crash recovery and immutable Registry/PermissionGate + trusted clock / audit-before-action mock integration only after prerequisite exact-head GREEN. JARVIS overall **NOT_PASSED**.


## Package D — Disconnected mixed-recovery class-custody hardening

**Additional production source:** `src/ark/agency/disconnected_write_recovery_fence.py` commit `9449966bbd14733d79144f6cd23a637ebd1ac33d`.

A frozen/slotted synthetic `OfflineRecoveryStepClaim` can still have its **class-level fields or lookup hooks** replaced by another local Python callback. Existing `_require_original_fence_denials()` pinned only some output constructors and deny-only properties, so Python field access could invoke substituted code during disconnected recovery classification. The revised guard pins **import-original exact class identities** and field, constructor, allocation and lookup descriptors for the three carriers (`OfflineRecoveryStepClaim`, `OfflineRecoveryDisposition`, `OfflineRecoveryFence`). It checks before the original input scan, at each source/decision epoch and directly after constructing a disposition before dereferencing its fields. This is *local* safety only, not an arbitrary-process-control defense.

**New regression:** `tests/test_disconnected_recovery_original_carriers_run657.py`, commit `c4c4c2121bfc1d4f8ca26a466e67d04bfa6c952c`, **24 authored cases** (20 preinstalled field/lookup/constructor poisons, 3 reentrant JSON/hash-stage class substitutions, 1 unchanged UNKNOWN-WRITE control). Every malicious hook must remain uncalled; the normal WRITE remains quarantined and never gains permission or a verified result. No inherited `__new__` test pollutes shared pytest.

**Additional CI:** [source #42190772160](https://github.com/Iam-2squared/ark-ai/actions/runs/42190772160) and [new tests #42190877169](https://github.com/Iam-2squared/ark-ai/actions/runs/42190877169), **QUEUED / exact-head six-job GREEN not yet verified** at this appendix. The earlier five-path comparison pertains to **packages A–C only**; the complete A–D source/test comparison adds two non-UI paths. This invocation now authors **44 new cases** (12 + 3 + 5 + 24) and updates five existing audit receipt cases, not 44 measured PASS results.

## Actual intermediate CI failure (not silently GREEN)

[Source-only #42189516707](https://github.com/Iam-2squared/ark-ai/actions/runs/42189516707) was **6/6 FAIL**, specifically because the old Run415 tests expected five **preinstalled** malicious factory callbacks to run after COMMIT and leave a link. The strengthened source correctly refused them *before* COMMIT; all five expected the now-invalid `event_count == 1`. The immediately following normal Contents API commit `8385b73c...` updates those expectations to `event_count == 0`, no hostile factory invocation. Post-COMMIT rollback ambiguity is independently retained by the Run414 callback test. No safety guard was relaxed. Later corrected exact-head CI remains to be established on real jobs.
