# Run588 — Non-UI Memory CI repair, quarantine receipt denial custody and integration gates

This is **non-frozen engineering evidence**, not a change to any V1/V2/Local UI/Launcher
freeze, protected V2 final-evaluation gate, V3 approval, or external ToolBackend behavior.

Recorded at ordinary host clock: 2026-11-03T18:49:22.114Z (not independently attested).

## Saved work and exact source/test custody

1. **Memory pre-existing expectation repair**: Prior Run587 PR #8 checkpoint HEAD
   `9d714d3f42b2a5a1987254d63835d39896a642a2`,
   [CI #41689129498](https://github.com/Iam-2squared/ark-ai/actions/runs/41689129498)
   FAILED all six jobs for the same existing
   `tests/test_memory_event_alignment_run507.py::test_orphan_terminal_event_is_rejected`
   regex expectation. Ubuntu Python 3.12 reported **7,709 PASS, 1 SKIP, 1 FAIL**;
   Windows 3.12 **7,650 PASS, 60 SKIP, 1 FAIL**. Global append-only event-ID
   gap detection now rejects the deleted CREATE event *earlier* than the previous
   orphan-lifecycle diagnostic. The test was amended to accept either explicit
   fail-closed diagnostic. **No Memory source/DDL/contract weakened**.
   Normal Contents API repair commit: `8254de8639f8874ed02f743350bfe92667721fab`;
   [CI #41696189075](https://github.com/Iam-2squared/ark-ai/actions/runs/41696189075)
   was Ubuntu 3/3 GREEN with Windows in progress at intermediate observation.
2. **Quarantine original authority descriptor custody**:
   `src/ark/disconnected_schedule_quarantine_ledger.py` source commit
   `fb9087615f671e84f884c4f0c67d4b01baacbfc8`.
   Original import-time `QuarantineReceipt` False-only authority property
   descriptors and `QuarantineWitness.independently_authenticated` are now
   independently pinned and checked again at the **final return boundary**.
   An already substituted property returning False is not silently promoted
   to the original denial. This post-COMMIT guard never refunds a committed
   synthetic quarantine row, never dispatches, and never auto-replays an UNKNOWN.
   Existing callback/fault-injection tests intentionally preserve their
   post-COMMIT diagnostic semantics.
3. **7 new parameter-expanded pytest cases**:
   `tests/test_quarantine_original_denial_descriptors_run588.py`, written at
   `e22ede789cb6836af6c32aaceffbbdbe45da48f4`;
   five preinstalled False-only receipt overrides, one witness-authentication
   override and one normal restart/inert-result control. This tests the negative
   property of unauthorized authority, not real permission issuance.
   The initial source+test CI found a Ruff **I001 import-order** problem, not
   a safety-gate regression. Follow-up normal test-only corrections:
   `c00d753528aac91a0971d09830b1949a36c215d9` and
   `6dc3533caf125f1bec7f52783a020b88fa6f3187`.
   [CI #41697264358](https://github.com/Iam-2squared/ark-ai/actions/runs/41697264358)
   was IN PROGRESS at this note's preparation. The 7 authored cases are
   **not independent local pytest PASS**, and the latest all-six matrix is
   **NOT YET GREEN** until checked for that exact HEAD.

## Next integration contract preparation (no executable backend authorization)

The existing registry, occurrence, audit and mock-plan surfaces are **separate**
local SQLite/review domains, not one atomic external-action protocol. Before a
real WRITE path or proactive dispatcher could safely be considered, an isolated
reversible non-UI bridge must satisfy these *testable* obligations:

- **Identity**: exact immutable `ToolRegistration` and registry revision must
  be bound to an exact `ToolCall` request ID and action effect; mutation,
  source drift or registry mismatch is a denial, not a lookup fallback.
- **Authorization**: exact-type `PermissionGate` decisions and a one-shot
  authorization must bind the same subject, capability, scope, arguments hash,
  occurrence and expiry. Caller-supplied booleans, local witnesses and mock
  receipts cannot assert actual consent, issuer authenticity or trusted time.
- **Audit before action**: one durable intent/occurrence reservation and
  pre-dispatch audit commitment should exist before an effect can be attempted.
  The mock executor must never be mistaken for a production tool backend.
- **Crash semantics**: after RUNNING or an ambiguous post-commit outcome,
  a restart moves the operation to manual-only **UNKNOWN / quarantined**,
  not back to PENDING or an automatic retry. Cross-file partial commits
  remain observable and block dispatch.
- **Evidence**: test startup, races, process crashes, immutable source
  substitution, post-COMMIT callback drift, clock rollback, tamper, and
  retained-prefix changes on Ubuntu/Windows Python 3.11–3.13. Only exact-HEAD
  six-job CI proof qualifies a revision for further dependent integration.
- **Human gates**: no live tool access, credentials, physical-PC assumption,
  real Candidate, protected V2 evaluation, paid API/GPU, automatic promotion,
  frozen-contract edit, UI work or main merge without explicit approvals.

These are **acceptance criteria for later implementation**, not proof that
trusted actors, physical exactly-once side effects, external independent
witnesses, real authorization, or production readiness now exist.

## Next plan / 今後の方針

1. Verify latest PR #8 exact-head six-job CI; repair observed failures only
   through ordinary permitted GitHub source/test writes, without bypass.
2. Continue disconnected restart-safe ToolRegistry/PermissionGate/
   audit-before-action integration, preserving UNKNOWN quarantine and no
   live backend execution.
3. Strengthen independently retained Memory row/event/CAS/expiry witnesses,
   Planner FAILED/BLOCKED recovery, Personal Context revocation, Scheduler
   deduplication, observation fixture lineage and strictly free V3 guards.
4. Keep PR #5/#8/#9 Draft and unmerged; keep PR #9 UI branch untouched.

**Completion: ARK/JARVIS/V3 NOT_PASSED. UI PAUSED. FREE-ONLY.**
