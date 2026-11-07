# ARK AI — Non-UI core final-callback custody, 2026-11-03 JST

## Scope and safety

This work is intentionally **local-first, disconnected and non-authorizing**.
It neither opens protected V2 final evaluation nor performs real Candidate training,
GPU provisioning, paid APIs, tool dispatch, notifications, main merge or UI work.
Frozen Memory and Planner contracts are not modified. PR #5 and PR #9 remain
Draft/unmerged and untouched in this package.

## Three independent implementation packages

1. **Planner transition return integrity**, source commit
   `0874a7238c2cb00649ce34297c34275e01276ae8`:
   `PlanGraph.transition` now verifies its pinned authoritative state and
   the exact detached `PlanStepStatus` immediately after the final
   `dataclasses.replace` callback. Previously, a reentrant final copy could
   return forged SUCCEEDED evidence or mutate the in-memory map after its
   last status-epoch publication. A rejection is **not** an atomic rollback,
   persistent recovery, or permission to retry a plan.
2. **Memory ambiguous-COMMIT review receipt integrity**, source commit
   `17870c3c7be8404910e486e985026938116bcfd5`:
   a detached `MemoryAmbiguityPair` is rechecked after **each** deny-only
   property, including the final getter. The final getter must not rewrite
   local digest fields after the last field precheck. Neither matching
   evidence nor a locally computed hash proves the caller committed, trusted
   time, actor identity or safe automatic retry.
3. **Registered ToolRegistry/PermissionGate implementation identity**,
   source commit `cb66e772295ae16943f0a68e35669575739b6cae`:
   the exact class-level registry `bind`, `resolve`, `revision`
   descriptor and registered policy `authorize` method are pinned at import.
   Registered authorization checks their identity before its first binding
   and again across grant callbacks and the token-spend boundary. An
   instance shadow of `PermissionGate.authorize` can no longer replace the
   exact-class policy used by `authorize_registered`.
   This remains an in-memory token set and *cannot* guarantee durable
   approval, authenticated grants, a trusted clock, or exactly-once external
   effects. Direct standalone `PermissionGate.authorize` is not changed.

The new regression file
`tests/test_non_ui_core_final_epoch_run579.py`
(commit `f59823d3bb94f6978c0bebe9bb57e774d4517494`)
contains **12 authored pytest cases**: Planner 3, Memory 3,
registered policy 6. It exercises reentrant reflected changes, class-level
implementation substitution, grant-iteration drift, normal FAILED/BLOCKED
Planner propagation, unaffected manual-only Memory review and exact-class
WRITE token consumption. **Authored tests are not independent local PASS.**
The final exact-head Ubuntu/Windows Python 3.11–3.13 CI verdict must be
retrieved from GitHub Actions; intermediate GREEN on older HEADs does not
validate these new changes.

## Boundaries, unresolved engineering issues

- All code remains reversible within the Draft JARVIS foundation branch.
- A malicious process with arbitrary Python reflection can still corrupt
  other objects or audit stores; import-time method pinning is local
  *drift detection*, not a hardened sandbox or provider attestation.
- In-memory Planner publication can precede an ultimately rejected detached
  result; treat that result as **UNKNOWN** and recover against an independently
  retained journal, not via automatic retry.
- A local Memory reconciliation receipt cannot establish a particular
  writer's COMMIT, provenance or consent; unknown outcomes remain
  **manual quarantine**.
- Registered READ decisions and process-local WRITE token spending are not
  persisted audit-before-action proofs; the real backend stays disconnected.
- No new UI/frontend source, tests, integration or branch work was performed.
  PR #9 must remain untouched until explicitly resumed.

## Next plan / 今後の方針

1. Resolve the final exact-head CI on both PR #8 and PR #5 (all six jobs).
   Fix any failures via the normal GitHub Contents API only, without
   weakening contracts, and keep work on independent non-UI modules while CI runs.
2. Continue Memory CAS / generation ABA / expiry and uncertain-COMMIT
   dual-observer evidence with authentic privacy lifecycle gates.
3. Extend Planner FAILED/BLOCKED restart and registered READ receipts;
   prove immutable registry identity, exact PermissionGate and durable
   audit-before-action before integrating any executable backend.
4. Improve scheduler restart occurrence/replay safeguards, privacy-safe
   Personal Context and mock Observation adapters. Maintain free-only V3
   approval/path/identity/reproducibility protection and all frozen gates.
