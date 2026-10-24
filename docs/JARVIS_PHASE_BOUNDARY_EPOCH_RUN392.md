# ARK local snapshot / proactive / observation phase-fence review — Run392

**Status:** disconnected, FREE-only synthetic contracts and test fixtures. This note is
engineering context, **not** approval for real execution, personal-data reuse,
media capture, notification dispatch, protected evaluation or model promotion.

## Motivation and exact changes

Some local reviewers previously verified frozen dataclass carriers only at the end of
a multi-phase operation. An injected callback could change a request, source or
witness during an earlier phase and restore its original value before final
validation. Even if the selected data stayed unchanged in a particular
fixture, that leaves an unjustified assumption of stable inputs across work.

1. `src/ark/memory/coherent_snapshot_review.py`: pin the originally chosen
   source Path **object**, request scalar types/values, and per-namespace
   `MemoryScope` values. Compare these after schema and clock work, SQLite
   queries, row hydration and ranking, and before returning. Retain each
   hydrated MemoryRecord's in-memory identity, scope, content, metadata,
   version and lifecycle fields while producing the content-free witness.
   An altered hydrated record cannot be emitted under its old digest.
   Regression fixture: `tests/test_memory_snapshot_phased_epoch_run392.py`
   (**6 tests**). The v1 SQLite schema, CAS, TTL, digest payload version and
   read transaction's original snapshot isolation are unchanged.

2. `src/ark/proactive_synthetic_freshness_review.py`: pin receipt, exact
   synthetic policy fields, source Path identity and independently held trigger
   history witness; check **between** SQLite validation, history hashing,
   retained-prefix review and final policy recheck. A transient mutation during
   validation can no longer be undone in the next callback.
   Regression fixture:
   `tests/test_proactive_freshness_phased_epoch_run392.py` (**6 tests**).
   No notification and no proactive ToolBackend dispatch.

3. `src/ark/observation_reuse_review.py`: recheck the cached lineage receipt
   and each envelope's original identity immediately after the historical
   lineage pass and again after the current-age pass. A transient
   privacy/source/adapter/timestamp/content-hash change between passes is
   rejected, rather than being silently restored at the end.
   Regression fixture:
   `tests/test_observation_reuse_phased_epoch_run392.py` (**6 tests**).
   No camera/microphone, raw media or external disclosure.

4. `src/ark/agency/registry.py`: independent `resolve()` calls now
   validate a snapshot of the original ToolCall and its arguments mapping
   identity before lookup, after `get()`, and after the registry's original
   immutable-entry epoch check. In-memory mutation during direct resolution
   can no longer make a re-targeted ToolCall silently resolve as if it had
   always been the original request. Regression fixture:
   `tests/test_registry_resolve_epoch_run392.py` (**6 tests**).
   No backend execution, authorization grant, durable token issuance or
   permission to spend is introduced.

## Evidence discipline and limits

The fixtures intentionally use mutable-in-reflection Python dataclasses and
callback injection to surface local TOCTOU defects. These fences detect
**observed** phase-boundary drift. They are **not** protections from arbitrary
privileged in-process code, atomic interprocess reads, filesystem inode
replacement, clock attestation, cryptographically signed history, authenticated
user consent or a globally serializable read across different SQLite stores.

A coherent Memory transaction guards one SQLite database snapshot, not the
personal consent ledger in another database. Hashes are local continuity
metadata rather than externally held authenticity proofs. Prepared proactive
markers and observation lineage receipts never authorize real-world actions.

The tests are supplemental to frozen V1/V2/Local UI/Launcher evidence.
PR #8 stays Draft/unmerged. V3 PR #5 stays Draft/NOT_PASSED; protected V2
FINAL remains unopened. No Candidate, external GPU, paid API/service, new
credential, physical-PC operation, destructive action or main merge is involved.

## Integration gates / prioritized next steps

1. Verify exact GitHub commits against all six Ubuntu/Windows Python
   3.11–3.13 CI jobs; keep failures and fixes tied to their actual SHAs.
2. Advance the **cross-store restart/UNKNOWN WRITE mock reconciliation**
   (Planner, PermissionGate, Registry, Claim, Occurrence, ActionAudit), keeping
   unknown external effects non-retriable.
3. Add independent persisted witnesses and adverse-crash tests for Memory
   events/CAS/expiry and privacy-safe Personal Context revocation.
4. Prove authenticated approval, trusted time, OS-level source custody and
   backend idempotency/reconciliation separately **before** any real action.
   Synthetic PASS is never a substitute for those authorizations.
