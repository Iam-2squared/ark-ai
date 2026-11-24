# ARK V3 Run1327 — validate preflight report path before runtime probing

## Exact basis

- Parent: Draft PR #5, branch `research/v3-learning-evaluation`, work-basis `af54b19b0f45bfbf66b46c93fcef422f5b1cae9c`.
- Child branch: `research/run1327-preflight-report-path-before-runtime-20261125`.
- This package is a local ordering hardening change only; it does not open any protected evaluation or run a preflight.

## Finding and change

`run_preflight()` validated the authorization snapshot and common evidence, then imported/probed the installed Torch/GPU runtime before validating the requested new report destination. An invalid destination could therefore trigger runtime probing unnecessarily.

The flow now validates the exact new report path immediately after the frozen preflight-scope snapshot validation, before common evidence reads and before `_verify_actual_runtime()`. The destination is still revalidated by `_write_new_preflight_report()` immediately before creation, preserving the existing write-time path-custody check.

## Regression

A synthetic test supplies an invalid traversal path and replaces common-evidence verification and runtime probing with fail-fast sentinels. It requires denial after preflight-scope validation and before either sentinel. No torch import, model load, GPU, Candidate or real backend is invoked.

## Evidence boundary

No frozen V3 Contract 1, V2 evaluation boundary, dataset, provenance, contamination, reproducibility or Candidate semantics change. This is not authorization to open protected V2 evaluation, execute preflight/training, create/promote a Candidate, or use paid/external compute. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. PR #5 remains Draft/unmerged; PR #9 remains untouched.
