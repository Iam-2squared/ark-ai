# ARK AI — Run427 disconnected original-carrier custody and fault matrix

**Scope:** `research/jarvis-foundations`, Draft PR #8. **Work basis:** Run426
checkpoint `ba15f294a5d03b7287cfd29c96ccf90ea0eb9f63`. The opening checkpoint
CI **#1171 / 40200056740** and Run426 source CI **#1169 / 40199645724**
were independently observed **six of six SUCCESS** before these changes.
PR #5 stays Draft/unmerged/NOT_PASSED. This note is not trusted evidence
of a person, user consent, external action outcome, signed clock, global
cross-SQLite atomicity, or paid compute authorization.

## Four independently reversible packages (26 added pytest cases)

1. **Read-only WRITE recovery original-input epoch (+6):**
   `src/ark/agency/synthetic_recovery_triage.py` at
   `5bef3b88727d6eedca3de99f7e2278c83864f616`,
   `tests/test_triage_original_carrier_boundaries_run427.py` at
   `b83823fd90c893a2d83cd8860ad86b040db0b3ab`.
   Preserve original ToolCall tool/capability/scope, each PlanStep step ID
   and action fields, and every caller-retained witness field by Python
   carrier identity across PlanGraph and independent journal/ledger/audit
   callbacks. Derived ToolCall request_id and arguments_sha256 remain
   deterministic **value** comparisons because these are properties
   recomputed on access. Reentrantly replacing original text with a
   distinct equal-valued string must fail closed. No backend is called.

2. **Disconnected mock WRITE admission carrier epoch (+7):**
   `src/ark/agency/synthetic_mock_action_cycle_review.py` at
   `44badb791a1fe01b327cf07147b5b822a08ebf23`,
   `tests/test_mock_cycle_original_epoch_run427.py` at
   `429b5b474ae857fc4c2b693bb539d7ee3006dbc0`.
   Original PlanStep IDs, ToolCall subject strings and one-shot token
   fields must survive both synthetic recover() callbacks and post-RUNNING
   checkpoints. A replacement detected after the Planner RUNNING COMMIT
   leaves a durable **UNKNOWN** local WRITE, not a replay or rollback
   claim. No mock executor invokes a registered ToolBackend.

3. **Startup × Proactive independently observed component custody (+8):**
   `src/ark/proactive_startup_fence_review.py` at
   `39b98eeb3ccd1b4c05492474372fd3edd5683432`,
   `tests/test_proactive_startup_original_snapshot_carriers_run427.py` at
   `7039383e47984099c506c74fcbd546e87995bf18`.
   Previously reviewed StartupSnapshot and each ComponentResult, its
   nested identity strings, and caller-retained trigger row/digest
   carriers must remain the *same* objects after every independent
   readiness and trigger callback. Equal-valued replacements cannot
   promote a stale or altered local READY diagnostic. This never
   activates notifications or tools.

4. **Privacy revocation retained-witness custody (+5):**
   `src/ark/personal_context_revocation_continuity_review.py` at
   `5bcfd262b0f70b8b13876d4c4df6d8c7f95987f8`,
   `src/ark/personal_context_retention_recheck_review.py` at
   `cbd556b8b0f1308487db1e3723360c32fa04443c`,
   `tests/test_privacy_retained_witness_id_epoch_run427.py` at
   `57c7fbbfb4c662ade22624b5c7ce96ca2fc7deca`.
   A caller-held revocation `witness_id` must remain the exact original
   object during integrity/schema callbacks and all four inventory passes;
   equal-valued string replacement is an input-epoch change. No memory
   erasure, disclosure, consent assertion or backup deletion occurs.

## Fault / trust boundaries

| Fault injected | Required interpretation |
| --- | --- |
| Equal ToolCall/PlanStep carrier substitution during PlanGraph review | Recovery rejected; no dispatch/retry |
| Equal token carrier substitution before Planner RUNNING | Rejected before durable transition |
| Token replacement after committed RUNNING | Rejected, RUNNING/UNKNOWN stays durable |
| Equal StartupSnapshot component or retained Trigger witness replacement | Deny correlated READY/freshness diagnosis |
| Equal revocation-witness ID substitution during read/recheck | Reject privacy diagnostic; do not infer user consent |
| Normal unchanged fixtures | Deterministic local diagnosis only; all authority flags false |

All changes use normal GitHub Contents writes to the isolated Draft
branch. There were no schema migrations or edits to frozen V1/V2/Local
UI/Launcher evidence, Memory v1/ActionAudit v1 DDL, or V3 Contract 1.
No Candidate creation/promotion, protected V2 opening, real sensor,
notification, authenticated issuer/clock or external WRITE. No paid
API, GPU, subscription, credential or physical-PC action.

## CI verification (commit-specific, never extrapolated)

- **#1173 / 40203927071** on
  `b83823fd90c893a2d83cd8860ad86b040db0b3ab`:
  **COMPLETED SUCCESS, six jobs** at inspection.
- **#1175 / 40204075095** on
  `429b5b474ae857fc4c2b693bb539d7ee3006dbc0`:
  **IN PROGRESS** at inspection.
- **#1177 / 40204283407** on
  `7039383e47984099c506c74fcbd546e87995bf18`:
  **IN PROGRESS** at inspection.
- **#1180 / 40204494357** on
  `57c7fbbfb4c662ade22624b5c7ce96ca2fc7deca`:
  **QUEUED** at inspection. This is the final executable/test HEAD,
  **not** yet independently GREEN.
- Later engineering-document and canonical checkpoint commits each have
  their own exact-HEAD CI; no parent-CI equivalence may be asserted.

## Next independent no-cost priorities

1. Resolve any exact-HEAD CI failure via smallest semantics-preserving
   normal-path repair; preserve historical failed runs and do not duplicate CI.
2. Extend unknown/reserved PENDING WRITE quarantine through Planner,
   PermissionGate, Occurrence, ActionAudit and AuditLink, including orphan
   audit evidence and dependent READ bridges.
3. Review multi-process Memory CAS/expiry/revision and content-minimized
   coherent snapshots, retaining original v1 DDL.
4. Advance deny-only issuer/trusted-clock interfaces, privacy erasure
   review protocols and Observation/Scheduler fixtures without enabling
   real-world effects.
