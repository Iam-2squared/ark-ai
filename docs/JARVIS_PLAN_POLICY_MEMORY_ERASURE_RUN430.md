# ARK JARVIS offline invariants — Run430

**Exact opening branch HEAD:** `18dd1b1dd32640066d9df2354d0640dd264d8e33` (Run429 checkpoint; its distinct GitHub Actions run #1196 / 40211578363 has completed SUCCESS on all six jobs).  
**Work branch:** `research/jarvis-foundations` / draft unmerged PR #8.  
**Latest source/test work HEAD for this document:** `61514010715d36a92243a60d3d0e11fe47f42912`.  
**Scope:** deterministic synthetic/SQLite fixtures only. No real ToolBackend, clock trust anchor, external compute, notification, personal-data connector, candidate, evaluation or promotion.

## Package A: cross-step registry and RUNNING truth

Normal GitHub Contents commits:

- Source `8c359a482b5650df9e7ebd3dddb7aa9976831097` — `src/ark/agency/synthetic_write_plan_recovery_review.py`.
- Regression `206e80e02b618f26c7140915089e92947e87c0b8` — `tests/test_plan_recovery_identity_and_running_truth_run430.py` (+6 parameterized cases).

Plan-wide recovery now retains each WRITE's separately bound `bound_action_id` from the original immutable registry revision and compares it to the later per-step diagnostic. A reentrant synthetic callback cannot substitute a different bound-action identity while keeping request ID, step ID and registry revision valid. It also cannot mark a journal-recovered RUNNING WRITE `ambiguous_write=False`, nor fabricate ambiguity for a non-RUNNING step. Six fixtures cover both original journal states, both alterations and valid no-dispatch behavior.

**Consequence:** a per-step diagnostic cannot by itself suppress a known RUNNING root in the plan-wide uncertain-step set. This remains a disconnected local consistency rule; it does NOT prove side effects, authorization, a live issuer, or cross-SQLite atomicity.

## Package B: coherent Memory under real independent-process erasure

Normal GitHub Contents commits:

- First regression `e1326f52040800ec518f76ad312f7d3006a4931a`.
- Corrected regression `e82e21538b9c5b1c052d7f0ed5974ede9e116a78` — `tests/test_memory_cross_process_snapshot_erasure_run430.py` (+2 parameterized cases).

A separate Python process deletes or expires a record in each of two namespaces. The reader first anchors an SQLite read transaction before the child commits, so that the old coherent multi-namespace snapshot must remain unchanged. A fresh read must see both deletions and each namespace's own create/deletion or create/expiry event history. All SQLite databases are disposable local fixtures; there is no deletion of connected personal data, cross-file atomicity claim or consent inference. The test revision corrected the per-scope `SQLiteMemoryStore.events(scope)` call signature; the superseded commit's CI is not used as evidence for the corrected test.

## Package C: proactive policy validation reentrancy

Normal GitHub Contents commits:

- Source `b300df3a4488302e39ab3b9b31c365ee85181088` — `src/ark/proactive_synthetic_review.py`.
- Regression `61514010715d36a92243a60d3d0e11fe47f42912` — `tests/test_proactive_policy_validation_epoch_run430.py` (+5 parameterized cases).

The exact eight original policy field carriers are captured before validation. Each `_text` and `_int` callback is followed immediately by a carrier epoch check, including during direct `identity()` calls. This rejects a reentrant callback that substitutes an equal-value string or temporarily retargets another field then restores it at a later validation step. Stable identity remains deterministic. No scheduler worker, real notification or live policy authorization is started.

## Evidence boundaries and next engineering work

There are **13 new parameterized regression cases** across three packages. GitHub's existing public-repository CI is automatically triggered by the normal Contents writes; the exact final source/test CI result must be checked separately and must not borrow GREEN from an earlier commit. Historical unsuccessful or incomplete runs remain attributable to their own SHA. No duplicate workflow rerun is required.

Read-only PR #5 review at `d6d4c1954a85fc716b1c593ac55c85417912418f` confirms that unresolved preflight-runtime cross-bindings and lexical-vs-canonical export path aliases remain on the separate draft V3 branch. No changes are made there. Explicit approval, immutable materialized model/tokenizer hashes, dataset human review, reproducible runtime pins, provider-side billing ceilings and its hard stops remain controlling.

**Next plan / 今後の方針:** first inspect Run430 exact final CI; fix only genuine failures through permitted Contents writes. Then extend independent retained-prefix and multiple-WRITE orphan checks without replay; exercise Memory CAS/retention under real local process concurrency; strengthen privacy revocation lifecycle and deny-only verified-issuer/clock interfaces. Keep both PR #5 and PR #8 Draft/unmerged and preserve frozen V1/V2/Local UI/Launcher, Memory v1 SQL, ActionAudit v1 SQL, V3 Contract 1 and protected evaluation.
