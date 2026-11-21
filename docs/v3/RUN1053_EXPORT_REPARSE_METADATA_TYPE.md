# Run1053 — V3 export path malformed reparse metadata

## Exact work basis

- Parent: gated Draft PR #5, branch `research/v3-learning-evaluation`.
- Exact parent HEAD: `034c756345b218ce41770ffccad7390a17ec018b`.
- Child branch: `research/run1053-export-reparse-metadata-type`.
- Source: `src/ark/learning/export_plan.py`.
- Regression: `tests/v3/test_export_reparse_metadata_type_run1053.py`.

## Finding

The export path policy already pins its reparse attribute mask and rejects ordinary symlinks and Windows reparse-point bits. However, when a present `st_file_attributes` carrier was not an exact integer, the helper treated the reparse bit as absent. That allowed malformed metadata to continue into canonical path admission.

## Change

- Reject a present non-exact-integer reparse metadata carrier before path resolution.
- Preserve the absent-field default on platforms that do not expose Windows file attributes.
- Leave the pinned mask, canonical source/output separation, command-plan contents and no-execution boundary unchanged.

## Regression coverage

Synthetic tests cover boolean/null/string/float metadata carriers, the absent-field platform default, and rejection of malformed ancestor metadata before canonical resolution. No privileged Windows junction or real model path is used.

## Limits and frozen boundaries

This is local export-plan path admission, not atomic descriptor-relative traversal, immutable filesystem custody or hostile concurrent-writer protection. The export plan remains data only: no converter, quantizer, model, GPU, external service, Candidate, preflight, training, protected V2 evaluation or promotion is invoked. V3 Contract 1, V1/V2/Local UI/Launcher evidence, main and the paused UI branch remain unchanged.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed. PR #5 remains OPEN/DRAFT/UNMERGED; V3 remains NOT_PASSED.
