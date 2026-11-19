# Run1004 — V3 export path reparse-point admission

**Work basis:** Draft PR #27 exact head `e2d151ad8fc3d83090de92d363aa889b4105e56a` (CI #44591480005 GREEN 6/6). This is an isolated free-only child of PR #27, which itself targets gated Draft PR #5. No frozen V3 contract or parent branch is changed.

## Gap

PR #27's export-plan source and output path admission rejected POSIX symlinks, lexical parent traversal and overlapping roots. On Windows, a directory junction is a reparse point but is not necessarily reported by `Path.is_symlink()`. The input-root admission could therefore follow an alias before comparing the canonical source trees.

## Change

- Inspect every existing ancestor with `lstat()` and reject POSIX symlinks and Windows `FILE_ATTRIBUTE_REPARSE_POINT` entries.
- Inspect the input root itself without following it; require a directory and reject a reparse-point root before resolving it.
- Apply the same ancestor check to the new export destination's parent chain.
- Preserve the existing input-tree separation, deployed-model collision, no-overwrite and no-execution behavior.

## Regression coverage

Three synthetic no-follow-stat cases mark a normal directory with the Windows reparse-point bit while leaving its symlink mode unchanged: source root, source ancestor and output parent. They require rejection before path resolution or output creation. No privileged Windows junction is created.

## Limits and authorization

This is best-effort local path admission, not atomic directory-handle custody and not protection against hostile concurrent filesystem replacement after checks. It does not hash model weights, invoke a converter or quantizer, load a model, create an export directory, start training, generate a Candidate, open protected V2 evaluation, or use paid/external compute.

PR #5 remains Draft/unmerged; PR #27 remains unchanged. PR #9/UI remains paused and untouched. **Exact-head CI is pending until this child PR is opened; no PASS is claimed. Overall ARK/JARVIS remains NOT_PASSED.**
