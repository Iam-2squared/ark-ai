# Run547 — synthetic READ result and Memory expiry authority custody

Scope: reversible and zero-new-cost Draft PR #8 foundations. All inputs
are local synthetic fixtures. No ToolBackend, physical memory purge,
trusted clock, owner authentication, consent, notification, live file
disclosure, or external action is implemented or authorized.

## Coherent packages

1. **Synthetic detached READ result set**:
   `src/ark/agency/disconnected_result_budget.py` at
   `7a3657e1c22569f8dc82b8d2e8422c62589c15e7`, test
   `tests/test_detached_read_result_denial_epoch_run547.py` at
   `a8492b6992d0b9947bf2606946225da1203c3188`.
   The bounded canonical-JSON result membership check now also pins the
   exact sealed receipt carrier, original non-authority property
   descriptors, and field identities across all three False getters.
   A True grant, even a replaced False descriptor, and post-verification
   receipt rewrite must fail closed. Synthetic hash receipts still do not
   authenticate any ToolBackend or external result.
2. **Privacy-focused Memory expiry candidate preview**:
   `src/ark/memory/expiry_candidate_preview.py` at
   `2b69e5d3b8ae6e0847d43ea3e0abe0cb9b274d96`, test
   `tests/test_memory_expiry_descriptor_custody_run547.py` at
   `6cc3777ed0164f5e3c0d183b5eeaf2e4ffef7a53`.
   Both read-only preview and retained-snapshot reinspection now
   require the original five privacy denial descriptors to survive
   every False-valued getter. A silently replaced False property is
   not considered sufficient evidence of consent, erasure or time.
   The schema, frozen Memory v1 contract and physical purge paths
   remain unchanged.
3. **CI failure diagnosis / smallest correction**:
   Earlier `tests/test_read_recovery_denial_descriptor_epoch_run546.py`
   correctly triggered `DetachedReadRecoveryRejected`, but expected
   only the specific `descriptor changed` diagnostic. In the actual
   fail-closed order the exception was `recovery schedule altered before
   return`. The test now accepts either explicit refusal without changing
   implementation semantics (`081f594fe86c6cd18ced6c6c2c7cf70b325c1e5f`).
   Ruff E501 was corrected with a multiline assertion
   (`283f96f6fe20223cd3d3db271b91265cdab6c7c6`).
   The additional new READ test import block was normalized at
   `6cec86a9fa83948b1a33c5a7555a51d247d215a4`.

## Regression coverage and claims

- Eight new parameter-expanded pytest cases for detached READ receipts:
  valid deny-only results, three forged True permissions, three replaced
  False permissions, and one mutation-capable callback.
- Eleven new cases for Memory expiry: valid empty bounded preview,
  five forged False descriptor cases on initial review, and five on
  retained snapshot reinspection.
- These are **authored**, not independently locally executed PASS.
  CI must be checked at the exact latest HEAD before a GREEN claim;
  an older passing run does not certify later source/test files.

## Trust boundaries and integration next steps

- Exact-type booleans and pinned Python object identities do not grant
  OS process isolation or independent persisted witness custody.
- Local SQLite and hashes cannot resolve an unknown post-COMMIT
  external effect automatically; WRITE replay remains quarantined.
- Integrate only after exact-head matrix CI verifies lower-level
  invariants. Follow-up priority is fail-closed Planner FAILED/BLOCKED
  recovery + READ Journal linkage, then trusted-clock audit-before-action,
  then private retention/revocation and local sensor fixtures.
- Do not modify frozen V1/V2/Local UI/Launcher contracts or protected V2
  evaluation, or perform paid compute, real Candidate generation or main
  merge absent separate explicit authorization.
