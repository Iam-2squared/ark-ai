# Run1051 — V3 identity reparse-policy pin

## Exact work basis

- Parent: gated Draft PR #5, branch `research/v3-learning-evaluation`.
- Exact parent HEAD: `034c756345b218ce41770ffccad7390a17ec018b`.
- Child branch: `research/run1051-identity-reparse-policy-pin`.
- Source: `src/ark/learning/identity.py`.
- Regression: `tests/v3/test_identity_reparse_policy_pin_run1051.py`.

## Finding

The local identity-manifest path guard recognized Windows `FILE_ATTRIBUTE_REPARSE_POINT`, but the module-level attribute mask was not pinned against rebinding. In addition, a present non-integer `st_file_attributes` carrier was treated as if the reparse bit were absent. This could turn a changed or malformed metadata policy into a permissive result in the local manifest admission path.

## Change

- Retain the import-time reparse attribute mask and reject a changed or non-exact-integer policy before reading metadata attributes.
- Treat a present malformed `st_file_attributes` value as a fail-closed metadata error.
- Preserve the portable absent-attribute default used on platforms that do not expose the Windows field.
- Keep symlink and valid Windows reparse-point detection unchanged.

## Regression coverage

Synthetic tests cover policy-mask rebinding before attribute access, boolean/null/string/float metadata carriers, the absent-attribute platform default, and rejection through `file_identity()` before opening the payload. No privileged Windows junction is created.

## Limits and frozen boundaries

This is local metadata admission hardening, not atomic descriptor-relative traversal, authenticated provenance, immutable filesystem custody, or hostile concurrent-writer protection. It does not materialize or hash any real model snapshot, invoke a converter/quantizer, load a model, access a GPU, contact an external service, generate a Candidate, open protected V2 evaluation, promote a Candidate, change Contract 1, or touch main/UI branches.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed. PR #5 remains OPEN/DRAFT/UNMERGED; V3 remains NOT_PASSED.
