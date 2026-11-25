# V3 Run1172 — Preflight evidence validator contract rebase

## Exact work basis

- Parent: gated Draft PR #5, branch `research/v3-learning-evaluation`.
- Exact parent HEAD at branch creation: `034a6f988445e54e5c6280d0f8f157959416d33b`.
- Child branch: `research/run1172-v3-preflight-validator-pin-rebase`.
- Source change: `src/ark/learning/preflight.py`.
- Regression: `tests/v3/test_preflight_validator_contract_run1172.py`.

## Finding and repair

The validation-only preflight path called `evidence.validate()` through a replaceable class method. A replaced public validator could run without the original validator being guaranteed as the final acceptance check. Field descriptors, dataclass field inventory, and class hooks also needed a pinned contract before evidence reads.

The change pins the exact PreflightEvidence dataclass field map/parameters, field descriptors, class hooks, and original validator. The public validator callback is still exercised for the existing mutation boundary, but the import-original validator always runs afterward. Instance-level validator shadowing, class/descriptor substitution, and field-inventory mutation fail closed before unsafe field reads.

Both direct measurement binding and the report/backend return paths use the same pinned validation helper.

## Evidence boundary

This is synthetic, validation-only hardening. No GPU is acquired, no model/tokenizer is loaded, no converter/quantizer runs, no Candidate is created, and no training or paid/external compute occurs. It does not open protected V2 evaluation, authorize Candidate promotion, or change the frozen V3 Contract. PR #5 remains Draft/unmerged; this child remains Draft pending fresh exact-head Windows/Linux × Python 3.11–3.13 CI.

No human review, hardware identity, runtime evidence, or V3 PASS is claimed. ARK/JARVIS remains NOT_PASSED.
