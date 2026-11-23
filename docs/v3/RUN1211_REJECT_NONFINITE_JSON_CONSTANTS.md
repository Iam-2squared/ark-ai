# V3 Run1211 — Reject non-standard JSON numeric constants

## Exact basis

- Parent: gated Draft PR #5 through Draft PR #387, branch `research/run1203-v3-dataset-duplicate-key-guard`.
- Exact parent work-basis HEAD: `a83edc9399d0c3895a3b4ac29d7bd99d406bf534`.
- Child branch: `research/run1211-v3-strict-json-constants`.
- The parent exact-head CI [45230249881](https://github.com/Iam-2squared/ark-ai/actions/runs/45230249881) was GREEN, 6/6. That result does not transfer to this child.

## Finding and repair

Python's default `json.loads` accepts `NaN`, `Infinity` and `-Infinity` even though they are not valid JSON values. The V3 canonical serializer already uses `allow_nan=False`, but the shared dataset/review parser did not reject those tokens on input.

The shared `loads_unique_json` parser now supplies a `parse_constant` rejection callback in addition to its existing duplicate-object-key hook. The rejection applies at every nesting depth and preserves ordinary finite JSON numbers. Existing dataset CLI, freeze and mock-training readers continue to share the same parser.

## Regression coverage

- Top-level array and nested-object occurrences of `NaN`, `Infinity` and `-Infinity` are denied.
- Finite positive, negative and zero numeric values remain accepted.
- Existing duplicate-key tests remain unchanged.

## Evidence and hard stops

This is a free local parser/input-integrity guard only. It does not create or approve dataset evidence, supply human-review decisions, start training, load model weights, generate a Candidate, open protected V2 evaluation, or change frozen Contract 1.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no local pytest/Ruff PASS is claimed. No paid/external compute, Candidate adapter/weight generation or promotion, protected V2 evaluation, credentials, new account connection, hardware, destructive operation, frozen-contract change, UI/frontend work or main merge. PR #5 remains Draft/unmerged; PR #8 and PR #9 remain untouched. ARK/JARVIS remains NOT_PASSED.
