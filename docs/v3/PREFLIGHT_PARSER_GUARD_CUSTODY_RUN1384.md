# Run1384 — V3 preflight parser guard self-custody rebase

## Exact basis

- Parent: Draft PR #5, branch `research/v3-learning-evaluation`.
- Exact parent work-basis HEAD: `279232c359ec13355f684e1c8cfc081bda0a4a94`.
- Child PR: Draft #563, branch `research/run1384-v3-preflight-guard-self-custody-rebase-20261125`.
- Source commit: `1ff7ec2bd4c4f84ab0c35f923c2e0472dd1d0c7f`.
- Regression-test commit: `73f88c104ec23504101ed802e7b8252d154ad729`.
- Rebased the isolated Run1375 guard correction onto the latest PR #5 head; predecessor CI does not transfer.

## Change and regression

The private preflight-report verifier retains the import-original JSON parser guard in a keyword-only default argument and compares both mutable module bindings against that retained reference before invoking the guard or parsing report bytes.

The synthetic regression replaces the helper and module alias with the same no-op, instruments the retained JSON loader, and requires denial before the loader is called.

The JSON loader, duplicate-key hook, non-standard constant rejection, finite-float policy, report schema, frozen execution snapshot and V3 Contract 1 remain unchanged.

## Evidence boundary

No model/tokenizer load, torch runtime, GPU query, preflight execution, training, adapter/weight generation, Candidate, protected V2 evaluation, credentials, hardware, paid/external compute, frozen-contract change, main merge or UI/frontend work occurred.

The source-only child head's workflow run `45576741530` was queued before the regression test was added; it does not validate the final child head. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No PASS is claimed. PR #5 and this child remain Draft/unmerged under the existing gate; PR #8/#9 remain untouched. ARK/JARVIS remains NOT_PASSED.
