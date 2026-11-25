# ARK Run1379 — Personal Context continuity guard self-custody

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `e212e77cb3432e0e226cebd4b9c1f2836eb064bc`.
- Parent source blob before the change: `7e1bd755b3f13f5db072951a208c49064249311e`.
- Rebased source blob: `51f786571a218228c5a95f17c7ca7f269d52d8f6`.
- Child branch: `research/run1379-context-continuity-guard-self-custody-latest-20261125`.
- Rebased from Draft PR #550 / Run1371. Its exact-head CI run `45552291666` was GREEN on the older parent only; it does not transfer to this exact base.

## Finding and correction

The retained revocation-continuity reader checked its hash, JSON, witness-carrier and schema-validator dependencies, but internal entry/recheck calls resolved `_require_original_witness_carrier` through its mutable module binding. A replacement no-op could bypass those identity checks before the private SQLite snapshot.

The module now retains `_ORIGINAL_WITNESS_GUARD`, checks that the mutable binding still names that exact function, and routes internal calls through the retained alias. A substituted guard is rejected before the ledger connection callback.

## Regression coverage

A synthetic regression replaces the mutable guard with a callback and requires the retained original guard to reject the replacement before either callback execution or private SQLite access.

## Scope and evidence limits

The revocation continuity schema, witness format, MemoryScope contract, public APIs, retention and denial-only semantics are unchanged. This does not establish authenticated consent, trusted time, independent storage custody, physical erasure, cross-store atomicity, an atomic downstream-use lease, or disclosure/dispatch authority.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No PASS is claimed before that run completes. Synthetic local SQLite only; no live personal data, paid/external compute, Candidate, protected V2 evaluation, credentials, hardware, destructive action, frozen-contract change, main merge, or UI/frontend work occurred. PR #5/#8 remain Draft/unmerged; PR #9 remains untouched.
