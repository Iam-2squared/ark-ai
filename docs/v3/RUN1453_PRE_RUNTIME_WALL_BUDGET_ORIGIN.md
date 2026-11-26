# V3 Run1453 — include runtime identity in the approved wall-time epoch

## Exact basis

- Parent: gated Draft PR #5, branch `research/v3-learning-evaluation`.
- Exact parent work-basis HEAD: `ea373c3496d06e2789cee5bb58836054ef35ed28`.
- Child branch: `research/run1453-v3-pre-runtime-wall-budget-origin-20261126`.
- Production files: `src/ark/learning/training_cli.py` and `src/ark/learning/hf_lora.py`.
- Regression: `tests/v3/test_pre_runtime_wall_budget_origin_run1453.py`.

## Finding and correction

Both CLI paths previously called `_verify_actual_runtime()` before the
`HfLoRAPreflightBackend` or `HfLoRAFullRun` constructed its
`WallTimeBudget`. Time spent importing the already-installed runtime,
collecting its identity, validating that identity, and completing preceding
CLI evidence checks therefore fell outside the approved wall-time window.

Each CLI path now creates one budget immediately after its scope-specific
execution authorization is validated. The same exact `WallTimeBudget`
instance is checked around evidence/runtime-identity work and passed into the
backend or runner. The runtime object continues that epoch through local
identity verification, model-load boundaries, and the existing later checks.
Direct backend/runner callers retain the prior fallback behavior of creating
their own budget when no budget is supplied. A supplied budget must be the
exact original `WallTimeBudget` type.

Preflight also checks the same budget after report construction and before
publishing the non-Candidate report. No execution-snapshot schema, authorization
scope, optimizer recipe, Candidate policy, or frozen contract changes.

## Regression coverage

A synthetic monotonic clock advances 30 seconds during a fake runtime-identity
probe and 31 seconds during fake local-identity verification against a
60-second budget. Both the preflight and full-training CLI paths must time out
at the local-identity boundary, before model/tokenizer loading. The test uses
no torch import, GPU query, model load, real preflight, training, or Candidate
path.

## Evidence limits

`WallTimeBudget` remains a cooperative boundary checker, not asynchronous
preemption: a blocking runtime-identity import/probe cannot be interrupted in
the middle of the call. The elapsed time is included, and the next check fails
closed before model/backend work continues. This does not prove hardware
runtime readiness or authorize execution.

No paid/external compute, model/tokenizer download, real adapter/weight
generation, Candidate promotion, protected V2 evaluation, credentials,
hardware, destructive operation, frozen-contract change, UI/frontend work,
or main merge is included. PR #5 remains Draft/unmerged; PR #8 remains
Draft/unmerged; PR #9 remains untouched. Exact-head CI is required; no PASS
is claimed.
