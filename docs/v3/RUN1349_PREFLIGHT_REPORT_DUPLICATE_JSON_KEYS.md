# V3 Run1349 — Reject duplicate keys in preflight reports

## Exact basis

- Parent: gated Draft PR #5, branch `research/v3-learning-evaluation`.
- Exact parent work-basis HEAD: `f7252fbe7d5f65c640fed41bbb5b3cc7ae817296`.
- Child branch: `research/run1349-v3-preflight-report-duplicate-json-guard-20261125`.
- Source change: `src/ark/learning/training_cli.py`.
- Regression module: `tests/v3/test_training_cli_preflight_duplicate_json_keys_run1349.py`.

## Finding and correction

The training-side `_verify_preflight_report()` used ordinary `json.loads` with only non-standard constant rejection. A hash-matching report could still contain duplicate object members at any depth; the standard decoder silently applies last-value-wins before runtime identity and evidence validation. The execution snapshot and dataset readers already reject duplicate keys, but this report reader did not.

The preflight-report parser now rejects duplicate keys recursively through `object_pairs_hook`, rejects non-finite exponent-overflow floats, retains non-standard constant rejection, and checks import-original parser/guard identities before parsing. Existing report schema, execution-core binding, evidence validation, report digest, authorization fields, and V3 Contract 1 are unchanged.

## Regression coverage

Synthetic byte fixtures cover duplicate root keys, duplicate nested runtime-identity keys, repeated member names in distinct objects, overflowing JSON floats, substituted `json.loads`, and substituted parser-guard refusal. The duplicate-key integration cases must fail before `RuntimeIdentity` construction. No Torch import, model/tokenizer load, GPU query, preflight backend, training, or Candidate path is invoked.

## Validation

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS or CI PASS is claimed at branch creation.

## Evidence boundary

This is free-only local parser hardening. It does not approve a dataset, create or promote a Candidate, open protected V2 evaluation, execute preflight/training, authorize paid/external compute, or change any frozen contract. PR #5 remains Draft/unmerged; PR #8 remains Draft/unmerged; PR #9 remains untouched. UI/frontend work remains paused. ARK/JARVIS remains NOT_PASSED.
