# Run1055 — V3 export path malformed reparse metadata rebase

## Exact work basis

- Parent: gated Draft PR #5, branch `research/v3-learning-evaluation`.
- Exact parent HEAD: `202cb5b6742a9f9e59c530b2c419decdb8f88c4d`.
- Child branch: `research/run1055-v3-export-reparse-metadata-rebase`.
- Source: `src/ark/learning/export_plan.py`.
- Regression: `tests/v3/test_export_reparse_metadata_type_run1055.py`.

## Finding and change

The export path policy pins its reparse attribute mask and rejects ordinary symlinks and Windows reparse-point bits. A present malformed `st_file_attributes` carrier was nevertheless treated as though the reparse bit were absent. This rebase fails closed on non-exact-integer metadata before canonical path admission while preserving the absent-field default for platforms without the Windows attribute.

The canonical source/output separation, command-plan contents, and no-execution boundary remain unchanged.

## Regression coverage

Synthetic tests cover boolean/null/string/float metadata carriers, the absent-field platform default, and rejection of malformed ancestor metadata before canonical resolution. No privileged Windows junction or real model path is used.

## Limits and frozen boundaries

This is local export-plan path admission, not atomic descriptor-relative traversal, immutable filesystem custody or hostile concurrent-writer protection. The export plan remains data only: no converter, quantizer, model, GPU, external service, Candidate, preflight, training, protected V2 evaluation or promotion is invoked. V3 Contract 1, V1/V2/Local UI/Launcher evidence, main and the paused UI branch remain unchanged.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed. PR #5 remains OPEN/DRAFT/UNMERGED; V3 remains NOT_PASSED.
