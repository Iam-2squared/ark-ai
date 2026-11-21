# V3 Run1056 — Preflight numeric-subclass boundary rebase

## Exact work basis

- Parent branch: `research/v3-learning-evaluation`.
- Exact parent HEAD: `c0ec757c9cdd240886d0008e3faec06beef8638b` (after the exact-head-GREEN Run1055 export-plan reparse guard integration).
- Child branch: `research/run1056-v3-preflight-numeric-tests-rebase`.
- Scope: validation-only tests and documentation; no source or frozen Contract changes.

## Finding and regression

The current preflight implementation already requires exact built-in numeric types for measured VRAM, allocated/reserved VRAM, wall time, frozen capacity, wall budget and VRAM tolerance. Existing tests cover booleans, non-finite values, overflow and range boundaries; this package adds the separate Python numeric-subclass callback boundary.

The tests use `float` and `int` subclasses whose `__float__` methods raise. They verify that all four `PreflightEvidence` measurements, measured `RuntimeIdentity.vram_gib`, frozen snapshot VRAM/wall budget and optional VRAM tolerance reject subclasses before conversion, while ordinary built-in synthetic measurements still pass validation-only binding.

## Validation and limits

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed. Deterministic synthetic identities/evidence only; no backend, GPU, model/tokenizer load, converter, quantizer, Candidate, training, protected V2 evaluation, promotion, payment, external compute, credentials, frozen-contract change, UI work or main merge is involved.

PR #5 remains gated Draft/unmerged. V3 remains NOT_PASSED.
