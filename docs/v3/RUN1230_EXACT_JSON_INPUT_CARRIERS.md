# V3 Run1230 — exact JSON input carrier admission

## Exact basis

- Repository: `Iam-2squared/ark-ai`.
- Parent: gated Draft PR #5, branch `research/v3-learning-evaluation`.
- Exact parent work-basis HEAD: `4810b0d93e1760bd72d5bc46d59673d6cb81da9b`.
- Child branch: `research/run1230-v3-json-exact-input-carriers`.
- Source, focused regression and this note are isolated from PR #5; no parent branch was modified by this package.

## Finding and repair

The shared `loads_unique_json` helper accepted a `str | bytes` annotation but delegated the value directly to `json.loads`. The standard decoder can invoke methods on subclasses while decoding (for example, text trimming or bytes decoding). That permits caller-defined callbacks to run inside the V3 parser before duplicate-key, constant and finite-float checks complete.

The helper now admits only exact built-in `str` and `bytes` values before calling the decoder. `bytearray` and subclasses are outside the declared contract and fail with `TypeError`. Duplicate-key rejection, non-standard constant rejection, finite-float parsing, canonical serialization and all dataset/approval semantics remain unchanged.

## Regression coverage

- Exact built-in text and bytes remain accepted.
- A hostile `str` subclass whose `lstrip` raises is rejected before the callback can run.
- A hostile `bytes` subclass whose `decode` raises is rejected before the callback can run.
- `bytearray` is rejected as outside the exact input contract.

## Evidence boundary

This is a free local parser-boundary hardening change only. It does not create or approve dataset evidence, make a human-review decision, start training, load model weights, generate a Candidate, open protected V2 evaluation, or change frozen Contract 1. No real training backend is invoked.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed. No paid/external compute, Candidate adapter/weight generation or promotion, protected V2 evaluation, credentials, new account connection, hardware action, destructive operation, frozen-contract change, UI/frontend work or main merge is included. PR #5 remains Draft/unmerged; PR #8 and PR #9 remain untouched. ARK/JARVIS remains NOT_PASSED.
