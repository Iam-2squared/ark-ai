# Run515 — Detached synthetic V3 paired-validation custody

> **LATEST Run515 V3 extension (source/test HEAD `03b5b452cfe7dcfdd11371c0d21a86b0edebfda2`):** The first package's `3d28263...` below is a historical, **already 6/6 GREEN** source head in [CI 41253908564](https://github.com/Iam-2squared/ark-ai/actions/runs/41253908564), not the current final source HEAD. The new fourth cross-lane package bounds the detached-only comparison's caller-held report text *before* validation callbacks: each scalar string is at most 4096 characters, with a cumulative cap of 32768 across **both** 30-case reports. It preserves validation semantics while rejecting oversized model/case/category identities and UTF-8-invalid content. The original `ValueError` catch also handles `UnicodeError`; no redundant exception clause is needed.

**Extension exact evidence:** source `src/ark/learning/detached_comparison_recheck.py` blob `574bfa59cb91c6e79b10bdda2dab34b04bcf0697`; tests `tests/v3/test_detached_comparison_text_budget_run515.py` blob `f398f62bf09fb57e7b6c26488bb0a66c8835b5df`, **7 newly authored parametrized/individual pytest cases**. Source+test latest HEAD `03b5b452cfe7dcfdd11371c0d21a86b0edebfda2`. The added input limit is for this independent, read-only verifier only; V3 Contract and underlying validation scorer are unchanged. This exact head's CI was not yet complete when this amendment was prepared; do not treat first package CI as newest source-head evidence. No Candidate, training, protected V2 opening, model/PC operation, paid API, billing approval or merge.

---

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
