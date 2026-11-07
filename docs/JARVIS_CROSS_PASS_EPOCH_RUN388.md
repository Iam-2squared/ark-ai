# ARK AI — Cross-pass epoch hardening (Run 388)

**Scope:** disconnected, reversible, FREE-only local synthetic/mock review paths on Draft PR #8. This document does not declare JARVIS PASS, real consent, trusted provenance, authenticated clock, backend effects, or external exactly-once delivery.

## Threat model

A frozen Python dataclass can be changed through reflection; a mutable store object may replace its SQLite `Path` object between otherwise valid subordinate checks. A reviewer that pins only within each subordinate call can accept a combination of independent reads from different input epochs, even when the replacement `Path` compares equal in value. Separately, a later callback may change the requested action or privacy-selection policy after an earlier review passed.

This work adds **outer-epoch deny-only fences**, without changing any SQLite schema, frozen evaluation contract, canonical model identity, or execution authority.

## Packages and targeted regression fixtures

1. **Retention inventory recheck:** `src/ark/personal_context_retention_recheck_review.py` pins Memory/veto `Path` object identity and original retained revocation-witness fields before the first of four inventory passes; verifies after each pass. The new `tests/test_retention_cross_pass_source_epoch_run388.py` covers both independent source objects after all four pass positions, reflected retained witness edits, and the non-authorizing stable path.
2. **Direct synthetic approval/recovery review:** `src/ark/agency/synthetic_claim_recovery_review.py` pins cancellation/Planner/ActionAudit/optional audit-link sources, Registry revision, and original ToolCall fields/argument-object before the first claim-veto check. It rechecks after the first veto, after recovery, and after the second veto. `tests/test_claim_recovery_outer_epoch_run388.py` covers source redirection after either callback, ToolCall field changes, and unchanged denied execution properties. The optional `SyntheticOccurrenceAuditLinkStore` uses its actual `_path` source field; preserving the original second-veto error taxonomy remains part of the behavioral contract.
3. **Fresh nonrevoked Personal Context:** `src/ark/personal_context_revocation_review.py` now pins Memory/veto sources and the ContextSelectionPolicy fields across retained-veto checks, coherent Memory read, context projection, and the final veto review. `tests/test_personal_context_fresh_outer_epoch_run388.py` checks intermediate same-string Path replacement and post-callback selection-policy drift, as well as a stable disconnected fixture. The ephemeral bundle **can contain private content**; its `action_authorized`/`dispatch_authorized` flags remain false.
4. **Proactive trigger / Startup Readiness:** `src/ark/proactive_startup_fence_review.py` now pins the actual `SyntheticProactiveLedger.path` object and retained trigger-witness values across two readiness and two trigger freshness passes, checking directly after each callback and before returning. `tests/test_startup_proactive_outer_source_epoch_run388.py` exercises each insertion point, late retained-witness mutation, and a stable non-authorizing trigger fixture. Neither a synthetic READY state nor a prepared trigger can send a notification.

## Exact-head evidence and failure ownership

The pre-work basis `33f772cee2b43ecff11cdd44978e4cbc160a78de` had CI #670 / run `40080220884`: all six Ubuntu/Windows Python 3.11–3.13 jobs GREEN, based on a fresh API/job read.

The new source-only claim-recovery head `5b30432147c7268d8d22bdb2248db642291a14a3` had CI #673 / run `40083595068`: **FAIL 6/6**. Its first failure was a mistaken optional sidecar attribute (`.path` rather than the existing `._path`), and its second was a premature generic claim-mutation rejection that displaced an existing `SyntheticApprovalRejected` expectation. These errors were found in the full pytest logs and corrected via ordinary GitHub Contents on `1d40c84cf8d8655ba5a7233eb56233ad8c6ec43c`, without weakening any deny check. Later CI #677 observed 1507 passed / 2 failed: the new Personal Context test patched a nonexistent module-level name for a continuity helper that is imported locally inside the reviewed function. Only the test patch target was corrected on `e003a929728c8874215b5c9a9e8b3df2404c4e4a`; the veto logic was not relaxed. A successful fix requires **new exact-head CI**; older GREEN evidence cannot be inherited.

The four source/test packages introduce **33 focused regression cases** (11 + 9 + 7 + 6) relative to the prior 1482-test baseline, subject to verification by exact-head pytest and Ruff. Intermediate CI results remain attached to their own SHA; they do not establish an eventual final-HEAD result.

## Safety and remaining gaps

- All code paths are local/read-only review or test fixtures; no external tool invocation, notification, media acquisition, real training, protected FINAL evaluation, Candidate generation/promotion, or paid compute.
- Comparing `Path` object identity is a **process-local reflected-mutation fence**, not a file-descriptor/OS-inode custody proof, a distributed lock, signature, or filesystem-integrity guarantee. A malicious OS-level same-path replacement, an ABA swap restored between observations, or an effect immediately after the final check remains outside scope.
- Multiple SQLite readers cannot prove a single atomic cross-database snapshot. Historical local hashes and revocation-witnesses require independent custody for meaningful rollback detection.
- Synthetic approval/cancellation evidence does not authenticate human issuer, subject, recipient, purpose, or clock. The audit log cannot certify that a backend WRITE occurred. **UNKNOWN WRITE remains non-retryable.**
- Preserve frozen V1/V2/Local UI/Launcher evidence and V3 PR #5 Draft/NOT_PASSED. No main merge or spending without explicit authorization.

## Next safe work

Confirm exact-head CI and repair only new semantics-preserving failures. Continue isolated Memory row/event/CAS witness checks, persistent Planner/Occurrence/ActionAudit diagnostic snapshots, privacy/veto lifecycle, and mocked Observation/Scheduler input contracts. Keep authenticated consent, trusted clock, OS custody, real backend effects and irreversible integration outside this research gate.
