# Run1116 — V3 code-tree no-follow traversal rebase

## Exact basis

- Parent: gated Draft PR #5, `research/v3-learning-evaluation`.
- Exact parent HEAD: `d9406b48c252065068d81dca55b77535073691a1`.
- Predecessor: Draft PR #16, `research/v3-code-tree-no-follow-run993`, exact head `83364e3c60276a233c0c724f410b7e1898624abd`.
- Predecessor exact-head CI: run [44549618760](https://github.com/Iam-2squared/ark-ai/actions/runs/44549618760) GREEN on its earlier base; that result does not transfer.
- Rebased child branch: `research/run1116-v3-code-tree-no-follow-rebase`.

## Change

Replace recursive `Path.rglob` enumeration with an explicit `os.scandir` stack. Each entry is classified using `DirEntry.stat(follow_symlinks=False)` before a directory can be queued for traversal. The existing exact-Path ingress, import-original stat/reparse policy, path-byte and entry-count budgets, metadata epochs, and deterministic relative-path ordering are preserved.

## Regression coverage

Synthetic tests verify that a symlink directory is rejected before its outside target is passed to `os.scandir`, a symlinked Python file is rejected, and the Windows enumeration path does not rely on `os.path.samestat`.

## Limits and safety

These are local no-follow prechecks and repeated metadata epochs, not atomic directory-descriptor custody or protection from a hostile concurrent filesystem writer. No model download, training, GPU runtime, Candidate generation, protected V2 evaluation, paid service, or main merge is part of this package. PR #5 remains Draft/unmerged.

**Fresh exact-head CI:** pending for this rebase; predecessor evidence does not transfer.
