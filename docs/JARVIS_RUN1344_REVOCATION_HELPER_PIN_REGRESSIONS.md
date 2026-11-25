# ARK Run1344 — Align revocation regressions with helper-identity guard

## Exact basis

- Parent: Draft PR #523, branch `research/run1343-personal-context-revocation-validator-custody-20261125`.
- Exact work-basis HEAD: `241a2f7ff6e0f21b73762b42a6dc228341ddc191`.
- New child branch: `research/run1344-personal-context-revocation-guard-tests-20261125`.
- Failed exact-head CI: [run 45513867238](https://github.com/Iam-2squared/ark-ai/actions/runs/45513867238), workflow run 7556.

## Finding and correction

Run1343 intentionally pins the import-original scope-digest helper and SQLite schema validator before invoking either helper. The first exact-head CI run exposed 15 stale regression expectations: older tests monkeypatched those helpers to simulate scope or path mutation and expected the injected callback to execute. The new guard correctly rejects the substituted helper before that callback can run, so the tests' previous error-message and callback-count expectations no longer described the enforced boundary.

This package updates those regressions to assert that substituted helpers are rejected before callback dispatch, that the original scope/path remains unchanged, and that no revocation row is written. It does not relax the helper-identity guard or alter the MemoryScope contract, revocation schema, DDL, retention, or privacy policy.

## Validation

- Run1343 exact-head CI [45513867238](https://github.com/Iam-2squared/ark-ai/actions/runs/45513867238): FAIL, 15 stale assertions across six matrix jobs; each job reached the pytest phase. No PASS is claimed for Run1343.
- Adjacent startup guard PR #522 exact-head CI [45513927591](https://github.com/Iam-2squared/ark-ai/actions/runs/45513927591): GREEN, 6/6 jobs; this is independent evidence and does not validate this package.
- Fresh exact-head CI is required for Run1344.

## Evidence boundary

Synthetic local SQLite and exact MemoryScope fixtures only. No authenticated consent, trusted storage, erasure proof, cross-store atomicity, downstream-use authorization, live personal data, external service or paid compute, Candidate, protected V2 evaluation, credentials, hardware, destructive action, frozen-contract change, UI work, or main merge. PR #8 and PR #523 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.

## Exact-head CI correction

- Initial Run1344 exact-head CI [45520692351](https://github.com/Iam-2squared/ark-ai/actions/runs/45520692351), head `0a68e7541f8e84e5dcff03fbe89a28638c28c7c3`: **FAIL at Ruff E501 only** across all six Windows/Linux × Python 3.11–3.13 jobs; pytest did not run. The findings were three overlong lines introduced while updating old regression expectations (two in Run416 and one Run402 docstring), repeated by the six matrix jobs.
- Corrected only test formatting and callback-count placement. The five regression files now have no lines over the repository's 100-character Ruff limit. No production source or test semantics were relaxed.
- Fresh exact-head CI is triggered by this correction; its result is pending. No PASS is claimed.
