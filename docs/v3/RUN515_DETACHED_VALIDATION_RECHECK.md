# Run515 — Detached synthetic V3 paired-validation custody

**Status:** validation-only, free-only local fixture work. V3, ARK, JARVIS: **NOT_PASSED**. PR #5 remains Draft and unmerged. No training, Candidate weight generation, external GPU or protected V2 evaluation.

## Exact work basis and file custody

- Work-basis HEAD: `4601abec9bce8cfae4cd3dea612bc395688f9b29` (Run514 final V3 source/test).
- Initial detached comparison verifier commit: `e7eddfe9e423497f9d49ac68be568775531ca72f`.
- Source order-binding fix: `8415a3eed5ac8c996a2bf084b94d513c4d06bfc2`.
- Test source commit: `4df870a9e15879e7d6bbb027fbc83b79f31775a1`.
- Final source+test HEAD after import-only fix: `3d28263f64657ea1f5463ab2b97c38514a97669c`.
- `src/ark/learning/detached_comparison_recheck.py` blob `f7737dcc9cabea194239b07a4e816563c3f7d57c`.
- `tests/v3/test_detached_comparison_recheck_run515.py` blob `22e9d76a9bed0aa903294adf7f71b07da7e22595`.
- This document and any later checkpoint are **different commit HEADs** from the final source/test HEAD.

## What is reviewed

`verify_detached_validation_comparison` accepts exact `ValidationReport` carriers with exactly 30 synthetic, ordered case identities, a separately retained byte artifact and an exact SHA-256 pin. It checks identity, category, case order, scorer/runtime/prompt contracts; freezes the original report and per-case carriers around callbacks; independently rederives regressions, improvements, runtime/memory failure counts, per-category results and non-authority fields; and byte-compares the canonical validation-only report before returning `None`.

An altered callback cannot silently suppress a regression, claim a protected V2 opening, promote a Candidate or launder an equal-valued replaced field carrier into an accepted historical observation. The retained SHA-256 is **not** an attestation of real model identity, real inference, human review, dataset approval or permission to spend. There is no model, local GPU or filesystem usage in this module.

**Authored tests:** 18 individual/parametrized pytest cases, including valid synthetic reports, malformed bytes/hash/type/size, differing identity/category/quantity/sequence, boolean corruption, duplicate cases, callback mutation, equal-value replacement, forged semantic result and protected-evaluation denial. Authored count is not independently run local pytest PASS evidence.

## CI custody

- [First full V3 run 41253820235](https://github.com/Iam-2squared/ark-ai/actions/runs/41253820235) at source HEAD `8415a3eed5ac8c996a2bf084b94d513c4d06bfc2`: **6/6 FAIL** due to Ruff I001 import-order formatting in the new test file. No pytest success inferred.
- Corrected the import-only expectation via the normal GitHub Contents API, preserving all detection and denial semantics.
- [Corrected V3 source run 41253908564](https://github.com/Iam-2squared/ark-ai/actions/runs/41253908564) at exact final source+test HEAD `3d28263f64657ea1f5463ab2b97c38514a97669c`: **IN PROGRESS / pending final matrix confirmation when authored**. Newer CI should be checked against its own exact commit before declaring GREEN.
- No independent full-checkout local pytest/Ruff was performed. No fabricated hardware, model, training or evidence identity.

## Immutable boundaries / Next plan

Do not modify frozen V1/V2/Local UI/Launcher, Contract 1, historical V2 suite or scoring budget. No external GPU or potentially billable action; no real Candidate/weights, automatic promotion, protected V2 opening, true human-review decision, credential setup, irreversible change or main merge. PR #5 stays Draft/unmerged under its controlling gate.

Next: confirm exact-source CI GREEN or fix verified failures without weakening checks; continue local-only reproducibility/path and provenance review; keep actual model bytes, reviewer approval, hardware identities and separate user billing authorization blocked until independently supplied.
