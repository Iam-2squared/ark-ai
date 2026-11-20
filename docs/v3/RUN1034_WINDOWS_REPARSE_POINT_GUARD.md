# Run1034 — Windows reparse-point rejection in local identity manifests

## Finding

The V3 local identity walker rejected POSIX-style symlinks but used `Path.is_symlink()` and `Path.rglob()` without checking Windows `FILE_ATTRIBUTE_REPARSE_POINT`. A directory junction is a directory reparse point, not necessarily a symlink. A recursive walker could therefore enumerate an aliased tree before the later symlink check.

## Change

- Detect symlinks and Windows reparse points from `lstat()` metadata.
- Reject reparse-point ancestors before opening individual identity files.
- Validate the snapshot root without following it.
- Inspect each yielded directory entry before advancing recursive enumeration, so a junction is denied before descent.
- Recheck entry type during the retained metadata-epoch pass.
- Add synthetic metadata tests for the Windows reparse attribute and no-follow ordering, plus a Windows-only disposable `mklink /J` integration test.

The file manifest format, SHA-256 construction, frozen V3 experiment identity, approval gates and pre-paid-compute boundary are unchanged. The guard only refuses path aliases that cannot be treated as ordinary local files/directories.

## Evidence and limits

All paths and bytes are synthetic local fixtures. The Windows integration test skips if the runner cannot create a temporary junction. This is not a hostile-writer-safe descriptor snapshot, authenticated provenance, remote revision attestation, or compute authorization. No download, model load, converter, quantizer, subprocess outside the Windows test fixture, GPU, training, Candidate, protected V2 evaluation, paid service, external compute, credential, promotion, or main merge is invoked. PR #5 remains Draft/unmerged.

**Work basis:** gated Draft PR #5 exact HEAD `fe7633e1fcfd8791ac36291f0cb89c615a4c7747`.
**Source/test branch:** `research/v3-windows-reparse-point-run1034`.
