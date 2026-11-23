# V3 Run1203 — Reject duplicate keys in dataset JSON

## Exact basis

- Parent: gated Draft PR #5, branch `research/v3-learning-evaluation`.
- Exact parent work-basis HEAD: `e7aed3f409ad6147260e6eb0bad2924eed5cf160`.
- New branch: `research/run1203-v3-dataset-duplicate-key-guard`.
- Exact child HEAD before PR creation: `fd5560c8c0f5dd997ce620a97bbe993f612ed325`.

## Finding and repair

The offline dataset CLI parsed reviewer-supplied candidate, flag and decision JSON with ordinary `json.loads`. Duplicate object members at any nesting depth were silently collapsed to the last value. That made the exact input bytes ambiguous before candidate validation, deterministic queue construction and human-review evidence binding.

The same permissive parser was also used when rebuilding accepted examples from the canonical dataset payload in the freeze and mock-training validation paths.

A shared `loads_unique_json` parser now rejects duplicate object keys at every nesting level. The dataset CLI uses it for all external JSON list inputs; freeze and mock-training dataset readers use it for canonical dataset payloads. Distinct objects may still use the same member name. Canonical serialization, dataset schema, frozen experiment parameters and approval/contamination rules are unchanged.

## Regression coverage

Synthetic tests cover nested duplicate keys, repeated names in separate objects, duplicate candidate fields in CLI input, and duplicate nested fields across the queue/freeze/mock-training dataset consumers. The mock backend remains a non-model receipt only.

## Evidence and hard stops

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no local pytest/Ruff PASS is claimed. This is a free local parser guard only. It does not create or approve dataset evidence, supply human-review decisions, start GPU work, create a Candidate, open protected V2 evaluation or promote anything.

No paid/external compute, Candidate adapter/weight generation, protected V2 evaluation, credential, account connection, hardware action, destructive operation, frozen-contract change or main merge. PR #5 remains Draft/unmerged; PR #8 and PR #9 remain untouched. UI/frontend development remains paused. ARK/JARVIS remains NOT_PASSED.
