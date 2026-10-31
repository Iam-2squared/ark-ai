# Run417 — Disconnected recovery, archive, registry and Memory carrier fences

This document records implementation scope and fault cases. It is **not a PASS,
authorization, attested outcome, clock signature or human-approval artifact**.
All components are isolated local synthetic/mock fixtures, with no external
backend, model, sensor, user data export or notification enabled.

## Work basis and isolation

- Initial exact branch HEAD: `a14015f2219676029b65915da9030ae8245c6a76` (Run416 checkpoint).
- PR #8 remains Draft/unmerged; PR #5 must remain Draft/NOT_PASSED.
- Existing frozen V1/V2/Local UI/Launcher evidence, V3 Contract 1,
  Memory v1 and ActionAudit v1 SQLite schemas are untouched.
- Current source/test work HEAD before this document:
  `c2c4297e1251da548a714bbb526ef8f321040eb2`.
- All changes stay on branch `research/jarvis-foundations`.

## Five source + regression packages

### A. Orphan pre-action audit after reservation loss

`src/ark/agency/synthetic_recovery_triage.py` and
`tests/test_recovery_orphan_preaction_run417.py` (7 parametrized cases).

When a pre-action audit event exists for an action but its durable reservation
is missing, the disconnected reviewer rejects the recovery, even if no
independently retained ledger witness exists. An unrelated request's event does
not change the result; a present reservation and matching audit remain inert.
If a sidecar audit link exists, its existing more-specific missing-reservation
diagnostic takes precedence before the new orphan check.

**Limits:** The additional audit read uses a second SQLite snapshot and cannot
establish atomicity across Planner, reservation, audit and link stores. It
rejects observed missing evidence; it never grants automatic replay or claims
an external action occurred. The final audit continuity recheck remains.

### B. Detached recovery archive strict identity and prefix shape

`src/ark/agency/synthetic_recovery_archive_review.py` and
`tests/test_recovery_archive_identity_shape_run417.py` (8 cases).

Locally re-hashed JSON archives must still carry exact lowercase
`act_<64hex>`, `tools_<64hex>`, `bound_<64hex>` identities; reference
orders must be canonical, occurrence counts cannot exceed retained ledger
row hashes and event links cannot point beyond the audit tail. Forging a fresh
local hash does not become authenticated provenance or grant a WRITE.

### C. Immutable ToolRegistry exact identity carriers

`src/ark/agency/registry.py` and
`tests/test_registry_equal_carrier_guard_run417.py` (24 cases).

Constructor, revision and public registration lookup/binding now reject
value-equal **different string objects** substituted by reflective mutation
into registered name/capability/backend ID, or the registry revision carrier.
Unchanged registrations preserve deterministic bound-action IDs. This is a
process-local tamper diagnostic, not backend binary attestation.

### D. Memory post-COMMIT CAS/return epoch

`src/ark/memory/sqlite_store.py` and
`tests/test_memory_post_commit_carrier_run417.py` (8 cases).

Recheck the original write/scope/metadata/source and store-path carriers after
leaving the SQLite commit context and after constructing the returned Memory
record. If a callback changes the caller's write *after* durable COMMIT, refuse
a clean return but preserve the committed row and matching event. **Never
claim a committed write was undone or retry it blindly.** No Memory v1 DDL
changes, external clock evidence or data export.

### E. Privacy revocation result witness carrier custody

`src/ark/personal_context_revocation_continuity_review.py` and
`tests/test_privacy_revocation_result_custody_run417.py` (5 cases).

The independently retained SQLite revocation review now pins the **newly
constructed result witness** (including exact row objects and witness-ID
carrier) through its final integrity check and read-only COMMIT. A mutation by
a synthetic validation/COMMIT callback fails shut before a result escapes.
This does not authenticate user consent, perform deletion, or atomically bind
Memory to the separate privacy veto store.

## Final source/test work basis

Five independent source+test packages add **52 parametrized pytest cases**
relative to Run416's 2349 cases. The final source+test HEAD before this
engineering documentation update is
`ec787df68ded8036c212304c3d28d25da1e8ed8f`, associated with
CI **#1068 / 40178924081**. At this document edit, success of its complete
six-environment matrix has not yet been established. The five packages were
written via the normal GitHub Contents API and no source gate was bypassed.

## Evidence and CI reporting rule

This initial document is prepared while exact-head CI is in flight. No whole
matrix GREEN is asserted here. Early source CI #1057–#1060 failed because the
new orphan check preceded the existing linked-reservation diagnostic and
changed a legacy test's expected error string. The source-only correction
`c2c4297e1251da548a714bbb526ef8f321040eb2` puts the new check after
sidecar link validation; rejection behavior remains fail-closed. Inspect the
*corrected source/test HEAD* and its own Ubuntu/Windows Python 3.11–3.13 jobs.
Any later failures must be recorded with their exact run, HEAD and cause.

## Next plan / 今後の方針

1. Verify/fix exact-head CI without weakening the denial semantics; retain
   failed-run evidence and switch independent lanes while CI is running.
2. Add retained-PENDING and UNKNOWN multi-WRITE partial-history fault matrices
   using independent SQLite snapshots, explicitly no replay.
3. Strengthen Memory concurrent CAS/expiry/snapshot and privacy revocation
   ordering while preserving existing schema and content minimization.
4. Continue offline trusted-clock/issuer, startup/observation/scheduler
   contracts and V3 free-only reproducibility/path checks; none confer live
   action permissions.

No paid APIs, GPU, new credentials, protected V2 evaluation, Candidate
generation/promotion, physical PC action, privacy deletion or main merge.
