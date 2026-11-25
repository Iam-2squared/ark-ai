# Run1126 — V3 code-tree import-original scandir custody

## Exact basis

- Parent: gated Draft PR #5, through Draft PR #294.
- Parent PR: #294, branch `research/run1116-v3-code-tree-no-follow-rebase`.
- Exact parent HEAD: `b8a1671d17d602276dadcacb970f554f9dcfa0b6`.
- New child branch: `research/run1126-v3-scandir-identity-custody`.
- Exact child HEAD at report creation: `0d2d2f4a47718d2a7d84da05d53b0796b7ef37c4`.

## Finding

The no-follow code-tree walk pinned the import-original `stat` module and file-type predicates, but still invoked the mutable module attribute `os.scandir` at traversal time. Replacing that attribute could substitute the directory enumerator before the no-follow `DirEntry.stat(follow_symlinks=False)` checks ran.

## Change

- Capture the import-original `os` module and `os.scandir` callable at module import.
- Include both identities in the existing fail-closed reparse-policy check, using function-default references so rebinding the module-level capture cannot silently redefine the baseline.
- Invoke the captured scanner on the production path.
- Retain a private explicit scanner parameter solely for deterministic synthetic traversal tests; public code-tree identity calls use the captured default.
- Migrate the symlink-directory and Windows reparse fixtures to that explicit private seam.
- Add regressions for substitution of both `os.scandir` and the module-level captured alias. Both must be rejected before the substituted callback is invoked.

No frozen V3 Contract, execution snapshot, authorization packet schema, dataset/provenance/contamination evidence, runtime identity or training recipe is changed.

## Validation boundary

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff or exact-head CI PASS is claimed here. The parent PR #294 exact-head run [45059989838](https://github.com/Iam-2squared/ark-ai/actions/runs/45059989838) was GREEN on its own prior head; that result does not transfer to this child.

This is an in-process dependency-identity guard, not a Python sandbox, atomic directory-handle custody, or protection from a hostile concurrent filesystem writer. The code remains local-files-only and does not download models, start training, generate Candidate weights, open protected V2 evaluation, promote a Candidate, or invoke paid/external compute. PR #5 and PR #294 remain Draft/unmerged.
