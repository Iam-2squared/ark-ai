# ARK JARVIS: detached recovery archive and Memory snapshot callback boundaries — Run396

**Disposition:** FREE-only, disconnected synthetic foundations under Draft PR #8. No real ToolBackend execution, user consent, external media, local-PC action, Credential connection, training, Candidate promotion, protected V2 FINAL evaluation or main merge. Frozen V1/V2/Local UI/Launcher contracts and Memory v1 schema remain unchanged.

## 1. Detached recovery archive: semantic consistency is not authenticity

`src/ark/agency/synthetic_recovery_archive_review.py` reconstructs an *independently held* content-minimized canonical JSON checkpoint without opening a database. The local checksum only detects unsynchronized change to archive bytes; a party able to replace both bytes and checksum can forge coherent metadata. It does not authenticate an issuer, the filesystem, a successful external WRITE, or human authorization.

Earlier shape checks admitted canonical, self-checksummed payloads with mutually incompatible values: `step_state="pending"` and `ambiguous_write=true`, repeated occurrence IDs, syntactically invalid occurrence IDs, and audit links with no corresponding occurrence. These are no longer treated as well-formed snapshots. The independent fresh SQLite reviewer still enforces retained prefix continuity when an archive is reopened. A locally `succeeded` Planner state never demonstrates the real backend outcome, and `running` is still ambiguous and must **never** be automatically replayed.

The witness format is not changed. This is a fail-closed validation change for objects that cannot arise from an unmodified legitimate `SyntheticRecoveryReview`. An audit link is still only cross-store **local** evidence; no cross-database transaction or atomic global snapshot is claimed.

Focused regressions: `tests/test_recovery_archive_consistency_run396.py`. They re-sign malformed local payloads with the same **untrusted** digest algorithm to demonstrate that the new validation catches contradictions even when the checksum passes.

## 2. Memory coherent snapshot: detect observable transients between callbacks

`src/ark/memory/coherent_snapshot_review.py` uses one SQLite read transaction and one caller-provided time sample. Input/request/scope and row carriers were already pinned, but before these changes the reviewer could defer a previously hydrated record check across several callbacks in a single namespace. A malicious or accidentally reentrant callback could temporarily mutate an earlier record and later restore it before the end-only check.

The new checks revalidate *all* previously hydrated records directly after each record hydration, before and after each lexical-scoring tokenization, and before and after each per-record witness metadata hash. The resulting selected records, ranking rule, frozen Memory v1 DDL, expiry behavior, and digest domain remain unchanged for stable inputs.

Focused regressions: `tests/test_memory_snapshot_callback_boundaries_run396.py`. Synthetic callbacks modify a prior record and schedule a later restoration. Correct behavior is to reject at the first observable intermediate boundary; stable snapshots remain deterministic. The digest is content-minimized but the returned `MemoryRecord` objects contain plaintext as the caller requested: this reviewer is **not** permission for Personal Context reuse or disclosure.

## 3. Privacy veto: check the original scope at each lookup boundary

`src/ark/personal_context_revocation_review.py` already queried its local veto journal without granting consent or performing erasure, but the direct `assert_not_revoked()` reader checked scope digests again only after all lookups. A synthetic reentrant callback could temporarily redirect a scope, or swap the journal's Path carrier and restore it during the next lookup. End-only comparison could accept a locally coherent but mixed-epoch absence observation.

The reader now pins each exact `MemoryScope` instance and original fields before any digest work. It rechecks original scopes and journal Path custody after each scope digest, immediately after SQLite schema checks and before/after each individual veto SELECT. Existing revoked-scope rejection and transaction rollback remain fail-closed. Focused regressions: `tests/test_privacy_veto_lookup_epoch_run396.py` (including successful stable absence, which is **not** a consent grant). The v1 local veto table is unchanged.

## 4. Proactive Scheduler: retained witness and per-row epoch boundaries

`src/ark/proactive_synthetic_continuity_review.py` reviews content-free hashes of persisted synthetic trigger rows under one SQLite read transaction. The earlier loop checked source and retained witness only after hashing *all* rows. A reentrant hashing callback on row one could briefly retarget the ledger Path or a separately held earlier witness and restore the original value on row two. The new row loop checks both boundaries around **each** row hash, and checks the exact original `row_hashes` tuple carrier as well as its values and digest. This is local witness consistency only, not trusted execution or external provenance.

Regression fixtures `tests/test_proactive_witness_row_phase_run396.py` cover a stable two-row history and three transient mutation variants: same-value replacement Path, changed retained digest, and value-equal replacement of the retained tuple. No notification, schedule dispatch, external effect or protected evaluation is invoked.

## 5. Threat ceilings / integration decision

Neither Python object identity nor a self-checksummed local archive proves independent provenance. Reflected in-process changes between checks, OS path/inode substitution, malicious recomputation, untrusted clocks, and independently committed cross-SQLite writes remain outside the proof boundary. No action/token is issued and no external effect is attempted. UNKNOWN WRITE remains UNKNOWN without automatic retry.

This implementation is **reversible and isolated**. Integration into live actions requires separately verified authenticated issuer, trusted clock, OS-level custody, audit-before-action, backend reconciliation/idempotency, and human approval. Until those gates are independently proven, keep both PR #8 and V3 PR #5 Draft/unmerged and report complete JARVIS as NOT_PASSED.

Evidence: exact SHA and each six-environment CI result belong to the canonical `docs/PROJECT_STATUS.md` checkpoint after direct observations. An earlier GREEN result is not inherited by later source/test/document/checkpoint commits.
