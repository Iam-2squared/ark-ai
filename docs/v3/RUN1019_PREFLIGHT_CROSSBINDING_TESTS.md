# ARK V3 Run1019 — offline preflight evidence cross-binding tests

**Work basis:** gated Draft PR #5 branch `research/v3-learning-evaluation`, exact HEAD `805b377697472268db02650a89c7a94b1c5337c8`. This is a test-only child; PR #5 remains OPEN/DRAFT/UNMERGED.

## Finding

The existing `verify_preflight_measurements` implementation already cross-binds evidence device, VRAM, tokenizer probe, allocated/reserved/capacity ordering and wall time to the measured runtime and frozen snapshot. Run514 added callback-epoch tests, but the explicit negative matrix in `docs/V3_FREE_GUARD_REVIEW.md` was not complete in the current PR #5 test tree.

## Regression

The new offline-only test module adds 41 parameterized cases for:

- evidence/runtime device mismatch;
- evidence/measured VRAM mismatch;
- tokenizer-probe mismatch;
- allocated VRAM above reserved VRAM;
- reserved VRAM above measured capacity;
- preflight wall time above the frozen budget;
- bool, NaN, infinity, zero and negative values across evidence measurements, measured/snapshot VRAM and the frozen wall budget.

No source, frozen V3 Contract, preflight authorization scope, compute gate or Candidate state is changed. Tests use deterministic synthetic runtime identities and evidence; no GPU or backend is called.

The tests are authored; no local pytest/Ruff PASS is claimed. Exact-head Windows/Linux × Python 3.11–3.13 CI is required.

## Limits

This closes a free test-coverage gap only. It does not authenticate the caller, hardware, tokenizer, costs, provider or evidence provenance, and it does not authorize preflight, training, Candidate generation, protected V2 evaluation or promotion. No paid service, external compute, credentials, frozen-contract change, UI, PR #9 or main branch is changed. PR #5 remains gated Draft/unmerged.
