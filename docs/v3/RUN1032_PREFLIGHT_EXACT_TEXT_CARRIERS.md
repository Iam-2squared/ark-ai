# Run1032 — exact text-carrier admission in V3 preflight evidence

## Finding

The validation-only `PreflightEvidence` record already requires an exact record type and exact numeric measurement types. Its `device` and `tokenizer_probe_sha256` fields used `isinstance(..., str)`, however, so a caller-owned `str` subclass could execute an overridden `strip()` before the evidence was rejected or proceed into regex processing.

## Change

- Require exact built-in `str` for the accelerator `device` field before calling `strip()`.
- Require exact built-in `str` for the tokenizer probe SHA-256 before regex validation.
- Preserve all existing value, digest, measurement, snapshot-epoch, and runtime-identity checks.
- Add hostile string-subclass regressions that fail if `strip`, `encode`, or `__len__` callbacks run, plus a valid built-in-string control.

## Boundaries

This is a free-only local input-integrity guard. It does not run a GPU, load a model/tokenizer, call a subprocess, create a Candidate, open protected V2 evaluation, or change V3 Contract 1. It does not authorize preflight, training, billing, export, or promotion. PR #5 remains Draft/unmerged; no UI or main-branch change is included.

**Work basis:** gated Draft PR #5 exact HEAD `15cb19af1ffb044d47e921d81c7495e5d3ce6163`. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no local pytest/Ruff PASS is claimed.
