# V3 Run1220 — Reject exponent-overflow JSON floating-point values

## Exact basis

- Repository: `Iam-2squared/ark-ai`.
- Parent: gated Draft PR #5 through Draft PR #387, branch `research/run1203-v3-dataset-duplicate-key-guard`.
- Exact parent work-basis HEAD: `be2824c8b52f223bd44a94bb200941d84bcb4e3a`.
- Parent exact-head CI [45252253193](https://github.com/Iam-2squared/ark-ai/actions/runs/45252253193) was GREEN, 6/6; that result does not transfer to this child.
- New child branch: `research/run1220-v3-reject-overflow-json-floats`.

## Finding and repair

The shared V3 parser already rejects duplicate object keys and the non-standard `NaN`, `Infinity`, and `-Infinity` constants. Python's standard `json.loads` can still parse a syntactically valid exponent such as `1e999` into positive infinity through the default float conversion path. The existing `parse_constant` callback does not see this token.

The parser now supplies a `parse_float` callback that converts the token and rejects non-finite results. All candidate, flag, decision, freeze and mock-training consumers continue to use the same shared parser. Ordinary finite values remain supported.

## Regression coverage

- Positive and negative exponent overflow at the top level.
- Nested exponent overflow in an object/list.
- Bytes input with negative overflow.
- Large but finite positive/negative values and a small finite value remain accepted.

## Evidence and hard stops

This is a free local JSON input-integrity guard only. It does not approve dataset provenance or human review, start training, load model weights, generate a Candidate, open protected V2 evaluation, or change frozen Contract 1. No real training backend is invoked.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed. No paid/external compute, Candidate adapter/weight generation or promotion, protected V2 evaluation, credentials, new account connection, hardware, destructive operation, frozen-contract change, UI/frontend work or main merge. PR #5 remains Draft/unmerged; PR #8 and PR #9 remain untouched. ARK/JARVIS remains NOT_PASSED.
