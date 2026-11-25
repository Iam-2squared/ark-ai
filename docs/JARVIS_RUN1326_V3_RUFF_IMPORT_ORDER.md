# ARK Run1326 — V3 merge-ref Ruff import-order correction

## Exact basis

- Parent: Draft PR #5, branch `research/v3-learning-evaluation`, exact work-basis `af54b19b0f45bfbf66b46c93fcef422f5b1cae9c`.
- Failed child: Draft PR #504, branch `research/run1324-v3-ruff-import-fix-20261125`, exact parent child HEAD `5e033e1cf0ea65b6c8931b2803851fc2e522b2fd`.
- Failed exact-head CI: run [45465726424](https://github.com/Iam-2squared/ark-ai/actions/runs/45465726424), run number 7522. All six matrix jobs failed at `ruff check .`; pytest was not reached. The Windows/Python 3.12 log identifies I001 in the three copied test files.

## Correction

The prior child description said import ordering was corrected, but its actual patch left `pytest` below first-party `ark` imports. This child branch makes the mechanical import-group correction in exactly these files:

- `tests/test_personal_context_replay_process_crash_run1033.py`
- `tests/test_planner_journal_terminal_hard_exit_run1280.py`
- `tests/test_tool_registry_delete_seal_run1240.py`

No test logic, production source, evaluation gate, dataset, provenance, contamination, reproducibility or Candidate behavior changes.

## Evidence boundary

This is a formatting-only child of the failed import-order package. The failed Run1324 result remains FAIL; fresh exact-head CI is required. PR #5 stays Draft/unmerged. No protected V2 evaluation, Candidate generation/promotion, paid compute, runtime probe, GPU, credentials, hardware, destructive action, UI work or main merge is authorized or claimed.
