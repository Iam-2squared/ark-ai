# ARK V3 — Run525: measured runtime exact-validator custody

## Source and test evidence

- Runtime identity guard change: `src/ark/learning/runtime_guard.py` at `88d1bfa861b38be7eee9da0dd82bc5035f787475`.
- New regression cases: `tests/v3/test_runtime_validator_method_bypass_run525.py` at `c6ebb543af3cc136099c07054576333ca65a0b5a`.
- Six newly authored pytest parameterizations/tests: five invalid measured VRAM identities and one matching synthetic baseline.
- The original `RuntimeIdentity.validate` method is now pinned at import. `verify_runtime_identity` retains the public validator callback (and epoch recheck for its mutations) and **also** invokes the original validation body, preventing a caller's replacement with a no-op from being the only check before interpreting measured VRAM.
- Synthetic negatives include exact-type violations (`True`, `False`, numeric text) and non-positive values that could otherwise fit within caller-specified measurement tolerance.

## Scope and controls

The code is a detached local runtime **comparison** safeguard. These tests construct dataclasses only. They do not import torch, inspect a real GPU, provision compute, download weights, train a Candidate, open protected V2 evaluation, promote, authorize billing or change the frozen Contract.

This integrity improvement is not a trusted runtime attestation or proof of an approved device. A Python process that can alter the module implementation itself remains outside the protection boundary. The original validator is captured at import, not cryptographically anchored here.

Six authored tests are **not** six proven passes. Exact test-head CI is required before any GREEN claim. The independently frozen model/tool bytes, dataset/human decisions, provider cost controls and explicit GPU approval remain unresolved.
