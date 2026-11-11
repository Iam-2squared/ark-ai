# ARK Run795 — Non-UI Proposal Lifecycle / V3 / Memory Expiry

**Work basis:** `60c05259d548a02271ea5835982e9ad79878c1dc`, Draft PR #8 branch `research/jarvis-foundations`. This technical record was prepared at **2026-11-12 00:54:52 JST** by an ordinary execution clock (not trusted time, human approval or external identity).

## Scope and saved GitHub work

1. **Proposal lifecycle (detached / synthetic)**: new `src/ark/agency/disconnected_proposal_lifecycle.py` at `89f19a82ed746778fde6424a504a669a6dd892ef`, corrected literal regex/domain escapes at `3ca426a30cd9a93376976fefa11853410294b91b`; tests `tests/test_disconnected_proposal_lifecycle_run795.py` saved at `1c9a3162a3daa474843cf66524435d938ce23f3e` (**20 submitted cases**, counting parameterizations). Deterministic proposal-only state replay, revision continuity, ordered hash chaining, independently retained prior-tip prefix comparison, terminal denials, exact types, bounded history and False-only human/training/code/eval/promotion flags. It cannot authenticate that any human reviewed a proposal. It creates no durable SQLite state and is not a full implementation of the proposal persistence contract. A content digest is not provenance.
2. **V3 free-only detached reviewer**: `src/ark/v3_detached_preflight_crossbind.py` at `9df66bf1a5a38c28475c45537aa35256577b156a`; `tests/test_detached_v3_numeric_protocol_run795.py` at `1712b382810d8ce8dd0a49f9f36c82019ed3e544` (**13 submitted cases**). Reject integers losing precision on conversion to floating capacity/time values; guard metadata limit, class lookup hooks, review field/constructor identities, check tuples after review. This is not Draft PR #5's frozen runtime preflight; it does not run GPU compute or change approval, identity, path, contamination, model weights or evaluation gates.
3. **Memory expiry integrity before private SQLite**: `src/ark/memory/expiry_candidate_preview.py` at `49c88db3ffe11930873e35d0ad5135692076b6f4`; `tests/test_memory_expiry_history_callbacks_run795.py` at `c9de60551869f6e7e51eb17825a2be055f2248bb` (**11 submitted cases**). Reject replaced global event high-water and due-event-chain validation callbacks and replaced row/event/time scan limits before opening private SQLite in both preview and verify. Existing local data, Memory v1 schema, expiry semantics and purge permissions are unchanged. No deletion authorized.

**Total 44 new parameterized test cases submitted** across 3 independently scoped non-UI packages. This count is not a CI PASS statement.

## CI, evidence and constraints

- Previous baseline `60c05259d548a02271ea5835982e9ad79878c1dc`: GitHub Actions [#43042981855](https://github.com/Iam-2squared/ark-ai/actions/runs/43042981855) **6/6 GREEN**, individually inspected before changes; this is prior baseline only.
- Proposal test commit `1c9a3162...`: [#43052349409](https://github.com/Iam-2squared/ark-ai/actions/runs/43052349409) **IN PROGRESS** at last inspection.
- V3 source commit `9df66bf1...`: [#43052473454](https://github.com/Iam-2squared/ark-ai/actions/runs/43052473454) **IN PROGRESS** at last inspection; V3 new test exact-head all-six result **UNVERIFIED**.
- Memory source commit `49c88db3...`: [#43052724942](https://github.com/Iam-2squared/ark-ai/actions/runs/43052724942) **QUEUED** at last inspection.
- Memory test/latest implementation commit `c9de6055...`: [#43052804299](https://github.com/Iam-2squared/ark-ai/actions/runs/43052804299) **QUEUED** at last inspection.
- No local `pytest`/Ruff, Windows physical machine or model runtime execution is claimed in this report. All six jobs must be examined on the corresponding exact HEAD; any failure requires real job log inspection and minimal semantics-preserving fix.

## Frozen and authority boundaries

All changes are limited to Draft PR #8. Draft PR #5 remains unmerged under protected V3 evaluation/payment/human-review gates; Draft PR #9 remains untouched with all new UI paused. Frozen V1/V2/Local UI/Launcher and V3 controlling contracts are not modified. No paid API/GPU/external compute, credentials, account connection, Candidate generation, promotion, protected evaluation, live tools, automatic UNKNOWN WRITE retry, destructive action or main merge occurred. Local simulated ACCEPTED_FOR_IMPLEMENTATION is not a recorded real approval, and does not grant ARK permission to edit code.

## Priority queue

1. Resolve this invocation's source+test CI on exact HEAD; if FAIL, inspect job logs, repair only the confirmed defect, then use an independent non-UI lane during CI.
2. Connect proposal-only replay to a separately reviewed durable CAS event store with privacy lifecycle and restart rollback detection; no synthetic reviewer should be treated as an approval authority.
3. Memory CAS/ABA, high-water and COMMIT-UNKNOWN manual reconciliation; Planner durable terminal/restart and UNKNOWN WRITE quarantine.
4. After exact-head GREEN foundations, revisit immutable ToolRegistry, exact PermissionGate and audit-before-action mock-only integration; no live action execution.
5. Keep reviewing privacy-safe Personal Context, proactive/observation backend contracts, and V3 free-only preflight guards. ARK/JARVIS overall **NOT_PASSED**.
