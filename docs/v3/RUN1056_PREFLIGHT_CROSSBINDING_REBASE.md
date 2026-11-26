# V3 Run1056 — Preflight evidence cross-binding test rebase

## Exact work basis

- Parent branch: `research/v3-learning-evaluation`.
- Exact parent HEAD: `c0ec757c9cdd240886d0008e3faec06beef8638b`.
- Child branch: `research/run1056-v3-preflight-crossbinding-rebase`.
- Scope: validation-only tests and documentation; no source or frozen Contract changes.

## Finding and regression

The current `verify_preflight_measurements` path cross-binds evidence device, VRAM, tokenizer probe, allocated/reserved/capacity ordering and wall time to the measured runtime and frozen snapshot. This package adds an explicit offline negative matrix for mismatched evidence and invalid numeric boundary values that was not represented by a dedicated current-branch test module.

The synthetic tests cover device mismatch, measured VRAM mismatch, tokenizer-probe mismatch, allocated VRAM above reserved VRAM, reserved VRAM above measured capacity, wall time above the frozen budget, and boolean/non-finite/zero/negative values across evidence measurements, measured/snapshot VRAM and the frozen wall budget.

## Validation and limits

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed. No source, frozen V3 Contract, authorization scope, compute gate or Candidate state is changed. No backend, GPU, model/tokenizer load, converter, quantizer, training, Candidate, protected V2 evaluation, promotion, payment, external compute, credentials, UI work or main merge is involved.

PR #5 remains gated Draft/unmerged. V3 remains NOT_PASSED.
