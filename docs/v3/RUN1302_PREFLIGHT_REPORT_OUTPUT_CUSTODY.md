# Run1302 — V3 preflight report output custody

## Exact basis

- Parent: gated Draft PR #5, branch `research/v3-learning-evaluation`.
- Exact parent work-basis HEAD: `ceb44c85e4bdd2b13cf62ddf02ccc9f555a51efc`.
- Child branch: `research/run1302-v3-preflight-report-output-custody-20261124`.

## Finding

The preflight report output path was checked only with `exists()`, `is_symlink()`, and `parent.is_dir()`, then written with `Path.open("xb")`. That rejects an existing final leaf but follows a symlink/reparse-point ancestor. The check also occurred after runtime identity collection and did not recheck the created file against an opened descriptor.

## Change

- Validate an exact native Path, bounded lexical path, existing real parent, and no symlink/reparse-point ancestry before any preflight backend work.
- Create with exclusive/no-follow flags where supported, then compare opened descriptor and path identity before writing.
- Recheck descriptor/path identity, regular-file type, link count, parent ancestry, and exact payload size after writing.
- Enforce the existing 1 MiB preflight-report budget on output as well as input.
- Keep this helper independently testable without torch, GPU, model loading, or preflight execution.

## Regression coverage

Synthetic temporary files only: successful bounded write, existing leaf denial, final symlink denial, symlinked parent denial before open, missing parent, lexical traversal, and invalid payload rejection before filesystem access.

## Evidence limits

Path-based ancestor rechecks narrow but do not eliminate hostile concurrent parent replacement; this is not atomic directory-fd traversal, authenticated provenance, fsync/power-loss evidence, or a filesystem sandbox. No real preflight, Candidate generation, training, export, Validation, protected V2 evaluation, or external compute was run or authorized. The PR #5 main merge-ref Ruff blocker remains outside this child and is not changed here.
