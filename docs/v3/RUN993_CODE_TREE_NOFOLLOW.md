# Run993 — V3 code-tree no-follow admission

**Work basis:** PR #5 exact head `805b377697472268db02650a89c7a94b1c5337c8`.

**Isolated branch:** `research/v3-code-tree-no-follow-run993`, proposed as a Draft child of `research/v3-learning-evaluation`. PR #5 remains Draft and unmerged.

## Change

The V3 local code-tree manifest previously used recursive `Path.rglob("*")` enumeration and rejected symlink entries after collecting paths. The manifest now uses an explicit `os.scandir` traversal and classifies each entry with `DirEntry.stat(follow_symlinks=False)` before a directory can be added to the traversal stack.

- Existing symlink directories are rejected before their targets are scanned.
- Symlinked files remain rejected.
- Unsupported filesystem entry types fail closed.
- Entry-count and UTF-8 path-byte budgets are preserved.
- Directory and file metadata epochs are rechecked after enumeration and hashing.

## Regression coverage

The new synthetic tests cover a symlink directory pointing outside the learning subtree and assert that the target directory is never passed to `os.scandir`, plus rejection of a symlinked Python file. They use only temporary local fixtures.

## Limits and safety

These checks are best-effort local filesystem checks. They do not provide atomic directory-descriptor custody or protect against a hostile concurrent filesystem writer replacing a directory between inspection and open. No model download, training, GPU runtime, Candidate generation, protected V2 evaluation, paid service, or main merge is part of this package.

**Exact-head CI:** pending; no PASS claim is made here.
