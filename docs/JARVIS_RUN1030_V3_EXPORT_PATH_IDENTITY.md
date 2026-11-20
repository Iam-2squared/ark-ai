# ARK AI Run1030 — V3 export path and executable identity guards

**Work basis:** gated Draft PR #5 branch `research/v3-learning-evaluation`, exact HEAD `325135c0c904cedb584f2edb67576aa992e2332f`. This is free-only validation/planning hardening; no runtime, converter, quantizer, model, GPU, training, Candidate or protected evaluation is executed.

## Rebased source and tests

- Carry forward the exact-native-Path admission and output path overlap/alias/symlink checks from PR #84.
- Preserve the exact built-in UTF-8 bounded `python_executable` admission from PR #87 before snapshot validation or file identity access; the value remains one argv element and is never shell-split or executed here.
- Include the focused hostile-PathLike callback regressions from PR #85 and the Python executable identity regressions from PR #87.
- Keep export planning data-only: no output directory is created and no converter/quantizer subprocess is started.

## Historical exact-head evidence (not transferred)

- PR #84 source head `ed1ca1c38ccdd72d5a310481737ba2fedcb6f961` / CI #44745421149: GREEN.
- PR #85 test head `0a3ce74726d483405a4f1fa97bb755ec8be8a74e` / CI #44745554160: GREEN.
- PR #87 source/test head `99ef7ef2e893ffb44970d82c67ce1df1240b7e9c` / CI #44757673921: GREEN.

Those runs validate only their historical exact heads. This new branch requires fresh exact-head CI; no local pytest/Ruff PASS is claimed.

## Limits

Path preflight is not race-free dirfd custody. No V3 Contract 1 change, paid service, external compute, model load, converter, quantizer, subprocess, Candidate adapter/weight generation, protected V2 evaluation, promotion, UI, PR #9 or main merge. PR #5 remains Draft/unmerged under its controlling gate.
