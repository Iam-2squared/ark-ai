# Run1035 — V3 passive packet read reparse-point guard

## Scope and exact work basis

- Parent: gated Draft PR #5, branch `research/v3-learning-evaluation`.
- Exact parent HEAD: `6b983be5734bc6b45dbc3d0e29a33593459f484f`.
- Source: `src/ark/learning/authorization_packet_file_review.py`.
- Regression: `tests/v3/test_authorization_packet_read_reparse_guard_run1035.py`.
- This is read-only local packet verification. It does not open preflight/training, write files, or authorize compute.

## Finding

The detached packet reader used `lstat`, final-component `O_NOFOLLOW` where supported, and symlink checks for ancestors. On Windows, directory junctions and other reparse points are not necessarily reported as symbolic links, and `O_NOFOLLOW` is not generally available. A path could therefore traverse a reparse-point ancestor despite the existing symlink-only checks.

## Change

Classify both symbolic links and `FILE_ATTRIBUTE_REPARSE_POINT` on the packet entry, opened handle metadata where exposed, and every ancestor using `lstat()`. Recheck ancestry after the read as well as before open, and during the existing independent final reread.

Synthetic tests prove that a reparse file and reparse directory ancestor are rejected before `os.open`, and that a reparse ancestor introduced between the two passive reads is denied.

## Limits

This remains repeated local metadata inspection, not an atomic dirfd traversal or defense against a hostile concurrent filesystem writer/kernel. The local packet hash is not user approval, provider billing evidence, Candidate authorization, trusted provenance, or permission to perform compute. V3 Contract 1 and all frozen evidence remain unchanged.

## Validation

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed. PR #5 remains OPEN/DRAFT/UNMERGED.
