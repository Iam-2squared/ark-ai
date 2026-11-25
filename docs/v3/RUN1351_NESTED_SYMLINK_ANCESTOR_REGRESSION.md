# V3 Run1351 — Nested symlink-ancestor regression

## Exact basis

- Parent: gated Draft PR #5, branch `research/v3-learning-evaluation`.
- Parent work-basis HEAD: `cff9cfb71e15fa7f614eec7674177bbf58f0aa27` (Run1349 parser guard integration).
- Child branch: `research/run1351-v3-preflight-nested-symlink-ancestor-20261125`.
- Regression: `tests/v3/test_preflight_report_nested_symlink_ancestor_run1351.py`.
- Production helper under test: `training_cli._validate_new_preflight_report_path()`.

## Finding and coverage

The existing report-path helper already walks every ancestor with `lstat()`; existing regressions covered an immediate symlink parent but not a real immediate parent reached through a symlinked grandparent.

The new synthetic test creates a real child directory beneath a symlinked grandparent and attempts to write a report through that alias. It requires rejection before `os.open`, preserves a sentinel file in the real target directory, and confirms no report file is created.

No production source, report schema, evidence digest, authorization scope, V3 Contract 1, dataset, runtime or evaluation behavior is changed.

## Validation

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. The Windows test may skip when directory symlink creation is not permitted; the Linux matrix exercises the positive symlink fixture. No local pytest/Ruff PASS or CI PASS is claimed.

## Evidence boundary

Synthetic temporary filesystem paths only. No torch import, model/tokenizer load, GPU query, preflight backend, training, Candidate creation/promotion, protected V2 evaluation, paid/external compute, credentials, hardware, destructive operation, frozen-contract change, main merge, or UI work occurred. PR #5 remains Draft/unmerged; PR #8 remains Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
