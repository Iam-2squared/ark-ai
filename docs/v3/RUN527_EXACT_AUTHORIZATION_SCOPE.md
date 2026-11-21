# Run527 — exact V3 execution authorization-scope boundary

Scope: free-only, local validation. **No GPU, model load, Candidate, paid compute, credentials, training, V2 opening, promotion or execution approval.**

## Change and test identity

- Starting PR #5 Draft/unmerged HEAD: `198f0a703ef805d0fde23a008974e54d9f2008fc`.
- Implementation: `src/ark/learning/execution.py` source HEAD `d4d2658edbb1c19e712cdb4251396254ae7c9f0c`.
- Regression tests: `tests/v3/test_execution.py`, source+test HEAD `9c197dd5d846d1ac4a44b4c37c55433d1a067c1d`.
- New pytest cases: **5 authored**, not an independent PASS count. CI for source+test HEAD is GitHub Actions [41299327848](https://github.com/Iam-2squared/ark-ai/actions/runs/41299327848); check the job matrix before assigning GREEN.

## Exact authorization input

Before touching the execution snapshot, `validate_experiment_001` requires a *plain str* scope in the closed set `none`, `preflight`, `training`. A `str` subclass with the same value and a custom non-string object forged to compare/hash as `training` are rejected. The input snapshot must be an *exact dict* (as produced by JSON decoding), not a dict subclass with replaceable mapping methods.

This is a narrowly scoped caller-input hardening, not a new authorization. All frozen experiment-001 sizes, optimization hyperparameters, independent review requirements, cost/compute hard stops and protected V2 final evaluation remain unchanged. The tests use synthetic in-memory snapshot dictionaries only and do not touch external services.

## Boundaries and future work

Python exact-type checking does not authenticate the source of authorization, model bytes, a human reviewer, a provider billing cap or a trusted runtime. The authorized preflight/training gates remain blocked by the existing unresolved identities and separate explicit approvals; PR #5 remains Draft and unmerged. Keep future runtime/gate tests disconnected until all frozen provenance and cost conditions can be satisfied legitimately.
