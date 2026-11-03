# Run514 — Offline V3 preflight measurement epoch, free-only audit

Status: **VALIDATION-ONLY; V3 NOT_PASSED; NO authorization to run preflight,
training, GPU compute, Candidate generation, protected V2 evaluation or promotion.**

## Exact source and tests

- Branch/PR: `research/v3-learning-evaluation`, [Draft PR #5](https://github.com/Iam-2squared/ark-ai/pull/5), unmerged.
- Run514 work-basis HEAD `67cd1d56823c7e0ffb9bd512833301d8749a4ce4`.
- Source+test HEAD `bc8d85d436b75312151a7ed46d0916a6494ca684`.
- `src/ark/learning/preflight.py`: blob `e768983b8a924ba6c5a36e21c14338b7b83ee19d`.
- `tests/v3/test_preflight_measurement_epoch_run514.py`: blob `330edf39e7b731851cb045aa0304bb0d3ee38fa2`.
- The frozen `docs/v3/CONTRACT.md` remains blob
  `b44f7b0e7e619c225ab662ed9c1fc8deae2b1e23`; no Contract rewrite.

## Change and evidence limitations

`verify_preflight_measurements` now requires exact `dict`,
`PreflightEvidence`, and `RuntimeIdentity` inputs, pins the complete nested
snapshot and measured evidence/identity carriers, and rechecks them after
validation callbacks and immediately before returning. Direct callers receive
an explicit fail-closed rejection of absent tokenizer/budget sections, invalid
frozen timeout types, nonfinite or nonpositive budget, and post-validation
mutations, rather than a false successful verification. The existing runtime
identity and peak/allocated/reserved/time mismatch tests remain binding.

**19 authored pytest cases**, including parameter expansions, cover synthetic
validity, subclass substitution, malformed carriers, mutation during evidence
and runtime callbacks, equal-valued field replacement, missing input sections,
numeric budget rejection and VRAM mismatch. These are source-authored cases;
they are **not** an independent local pytest/Ruff PASS and must be confirmed
by exact-head GitHub CI.

This function compares caller-supplied objects; it does not authenticate the
caller, frozen snapshot, measured GPU, tokenizer, costs or provider, and **never
calls a backend**. No external GPU/provider API, downloaded weights, actual
training or protected V2 evaluation was invoked. PR #5 remains Draft/unmerged
until the explicit controlling gate and real approved evidence are satisfied.

## Next plan / 今後の方針

Confirm all six CI matrix jobs for source+test HEAD
`bc8d85d436b75312151a7ed46d0916a6494ca684`. Continue independent
local-byte/path/identity and approval evidence safeguards only. Preserve
Experiment 001 and frozen V2 suite/scorer/policy. All real compute and
Candidate steps remain blocked pending explicit user approval plus exact
human review, pinning, resource/cost caps and provider-side safeguards.
