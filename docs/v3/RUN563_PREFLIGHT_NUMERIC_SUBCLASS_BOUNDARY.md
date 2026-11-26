# V3 Run1020 — Preflight numeric-subclass admission

**Work basis:** gated Draft PR #5, branch `research/v3-learning-evaluation`, exact HEAD `805b377697472268db02650a89c7a94b1c5337c8`. This is a validation-only test child; PR #5 remains gated Draft/unmerged.

## Finding

The validation-only preflight path already requires exact built-in numeric types for measured VRAM, allocated/reserved VRAM, wall time, frozen capacity, wall budget and VRAM tolerance. Existing tests cover booleans, non-finite values, overflow and range boundaries; this package pins the separate Python subclass boundary.

## Regression

The new tests use `float` and `int` subclasses whose `__float__` methods raise. They verify that:

- all four `PreflightEvidence` measurements reject subclasses before conversion;
- measured `RuntimeIdentity.vram_gib` rejects subclasses before conversion;
- frozen snapshot VRAM and wall-budget values reject subclasses before conversion;
- the optional VRAM tolerance rejects subclasses before conversion;
- ordinary built-in synthetic measurements still pass the validation-only binding.

The test is authored; no local pytest/Ruff PASS is claimed. Exact-head six-job CI is required.

## Limits

No backend, GPU, model, tokenizer download, converter, quantizer, Candidate adapter, weights, training, Validation/V2 opening or promotion is invoked. The V3 Contract and paid-compute gate are unchanged. No payment, external compute, credentials, UI, PR #9, or main merge.
