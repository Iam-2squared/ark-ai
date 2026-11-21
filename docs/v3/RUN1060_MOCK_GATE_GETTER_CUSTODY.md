# Run1060 — V3 mock-gate getter custody

## Exact work basis

- Parent: gated Draft PR #5, branch `research/v3-learning-evaluation`.
- Exact parent HEAD: `c23fa8f24cf3f3ae0ee079111cfc0984d8f63d76`.
- Child branch: `research/run1060-v3-mock-gate-getter-custody`.
- Scope: the non-authorizing `SimulationEvidence` mock-policy simulator only.

## Gap

The existing gate pinned a tuple of values through `getattr` and later checked the same values through `getattr`. A stable replacement `__getattribute__` could therefore return eligible-looking values while the instance dictionary retained a regression or other noncanonical evidence. The existing Run520 tests covered reentrant mutation, but not a getter that consistently spoofed the same field.

## Change

- Pin the exact evidence class, field tuple, class access hooks and class-level field descriptors at import time.
- Read the exact built-in instance dictionary through `object.__getattribute__`, bypassing a substituted instance getter.
- Require the exact expected field-key set and retain the dictionary identity plus every field-value identity across policy evaluation.
- Reject a changed class hook/descriptor or unexpected instance state as noncanonical mock evidence.
- Preserve the existing result vocabulary and explicit `NOT_EVALUATED`, `automatic_promotion=false`, and `v3_gate=NOT_PASSED` outputs.

## Regression coverage

Three synthetic tests cover a stable getter that hides a stored regression, a class-level field descriptor replacement, and an unexpected instance-dictionary key. Existing Run519/Run520 exact-input and reentrant-mutation tests remain unchanged.

## Limits and safety

This hardens a local mock-policy diagnostic against accidental or test-injected Python-level accessor substitution. It is not a security sandbox against arbitrary code already executing in the process. No real evidence, model, Candidate, adapter/weight, protected V2 evaluation, paid/external compute, account credential, or external effect is used. V3 remains NOT_PASSED; PR #5 remains Draft/unmerged and Contract 1 is unchanged.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed.
