# Run1404 — V3 detached packet witness lookup custody

## Exact basis

- Parent: Draft PR #5, branch `research/v3-learning-evaluation`.
- Exact parent work-basis HEAD: `2c3501930baff61f04b25e7e02c00b0241a426e7`.
- Child branch: `research/run1404-v3-packet-witness-lookup-custody-20261125`.
- Child HEAD before this evidence document: `b19555396872c8156703fe4c0e31b9163914ce7d`.
- Source file: `src/ark/learning/authorization_packet_verify.py`.
- Source blob after implementation: `6bb0007c3f3b6b47d71e0d859267a4e800e4a27f`.

## Finding and correction

The detached packet verifier returned a frozen, slotted witness and repeatedly inspected its fields and denial properties. However, the witness class lookup hooks were not part of the retained class contract. An in-process replacement of `__getattribute__` or `__getattr__` could intercept those reads. The absence of a hook was also represented implicitly, so an explicit `None` was not distinguished from absence. The mutable denial-flag tuple could also be replaced to skip the final authority checks.

The verifier now retains the exact witness type, constructor, class-hook inventory and a unique absence sentinel in keyword-only defaults. It checks namespace membership separately from descriptor identity, pins the denial-flag vector and original denial descriptors, and retains the guard in the invocation's local frame across input/getter callback boundaries. Each witness field/denial read is bracketed by a class-contract recheck.

The existing field-descriptor callback tests remain meaningful: field getters are still exercised, and their input-mutation effects are checked by the existing snapshot/packet epoch validation. This change does not replace those tests with an earlier blanket field-descriptor denial.

## Regression coverage

- Explicit `None` for `__new__`, `__getattribute__`, `__getattr__`, `__setattr__` and `__delattr__` is denied.
- Hostile instance lookup hooks are rejected before execution.
- The exact absence sentinel installed as a hook is denied.
- Sentinel and equal-valued hook-name vector replacement are denied.
- An empty/replaced denial-flag inventory and a false-valued replacement denial descriptor are denied.
- Replacing the module guard during input-epoch callbacks is detected by the retained local guard.
- Existing valid packet, denial-descriptor and late field-getter mutation tests remain in place.

All new tests use invalid synthetic review inputs or in-process class monkeypatches. No model, tokenizer, GPU, network, paid service, adapter, Candidate, protected evaluation, or real training path is invoked.

## Scope and hard stops

This is local in-process review-witness integrity only. A matching packet hash remains neither authenticated user approval nor provider billing evidence. The witness continues to authorize no external compute, Candidate generation, protected evaluation or main merge. The frozen V3 Contract 1, packet schema, execution snapshot, dataset, training parameters, runtime identity and public authorization semantics are unchanged.

No paid/external compute, real Candidate generation/promotion, protected V2 evaluation, credentials, hardware, frozen-contract change, destructive operation, main write/merge or UI/frontend work occurred. PR #5 remains Draft/unmerged; PR #8 and PR #9 remain under their existing gates. Fresh exact-head CI is required; no PASS is claimed.
