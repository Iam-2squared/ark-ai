# ARK Run1282 — Disconnected startup readiness lease review

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `101be0cb505d8ae045027faf54f8d982c0a4f9d2`.
- Child branch: `research/run1291b-startup-readiness-lease-rebase`.
- Test-only package; no production startup evaluator, lease reviewer, schema, public API or frozen contract is changed.

## Coverage

- Exact freshness boundary, age rejection, expiry and clock rollback.
- Exact integer carriers; bool-as-int, negative and out-of-range values are denied.
- Exact requirement tuple/carrier types, duplicate/missing components and schema mismatch.
- Blocked dependencies cannot be hidden by a READY descendant.
- Reflected snapshot mutation and replaced requirement/result authority descriptors are rejected before a lease is returned.
- A valid lease younger than the configured maximum age is accepted.

## CI correction

The first exact-head run found two test expectation errors, not a production failure:
- `(now_ms=101, max_age_ms=100)` is a valid age (1 ms), so it was removed from the rejection matrix and covered by an explicit positive test.
- Replacing `dispatch_authorized` correctly triggers the earlier, stronger diagnostic `readiness result authority epoch changed before review`; the assertion now checks that exact guard.

A fresh exact-head CI run is required after this correction. No PASS is claimed until it completes.

## Evidence boundary

The lease is a synthetic diagnostic only. It is not proof of real startup readiness, trusted time, consent, notification permission, dispatch authority, hardware availability or automatic replay. All values are synthetic. No UI/frontend, paid/external compute, Candidate, protected V2 evaluation, credentials, hardware, destructive operation, frozen-contract change or main merge is involved. PR #5/#8/#9 remain under their existing gates; ARK/JARVIS remains NOT_PASSED.
