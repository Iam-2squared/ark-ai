# ARK Run1328 — V3 Ruff import-section separator correction

## Exact basis

- Parent: Draft PR #5, branch `research/v3-learning-evaluation`, work-basis `af54b19b0f45bfbf66b46c93fcef422f5b1cae9c`.
- Failed predecessor: Draft PR #506, branch `research/run1326-v3-ruff-import-order-correction-20261125`, exact HEAD `099f54af6dbc4a1d0099ff2fa43438477ffe0cdc`.
- Failed exact-head CI: run [45473771099](https://github.com/Iam-2squared/ark-ai/actions/runs/45473771099); all six matrix jobs failed at Ruff I001 before pytest.

## Finding and correction

Run1326 moved `pytest` above the `ark` imports, but retained an extra blank line between them. The exact Ruff diff requests the third-party/test import to be adjacent to the `ark` imports in this repository's configured import classification. This child removes only that extra separator in the same three files; no import is removed or reordered across the standard-library boundary.

## Evidence boundary

Run1326 remains FAIL; no test result transfers. Fresh exact-head CI is required. No production source, test logic, V3 evaluation gate, dataset, provenance, contamination, reproducibility or Candidate behavior changes. PR #5 remains Draft/unmerged; no protected V2 evaluation, paid compute, runtime probe, GPU, credentials, hardware, destructive action, UI work or main merge.
