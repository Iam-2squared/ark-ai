# Run1035 — V3 authorization packet reparse-point ancestry guard

## Scope and exact work basis

- Parent: gated Draft PR #5, branch `research/v3-learning-evaluation`.
- Exact parent HEAD: `6b983be5734bc6b45dbc3d0e29a33593459f484f`.
- Source: `src/ark/learning/authorization.py`.
- Regression: `tests/v3/test_authorization_packet_reparse_point_run1035.py`.
- This is a local review-artifact path guard only. It does not create or validate an approval, open preflight/training, or write a Candidate.

## Finding

The authorization packet writer rejected symbolic links in the output path but did not classify Windows directory junctions and other reparse-point ancestors. Such an ancestor can redirect a nominally new output path even when `Path.is_symlink()` is false.

## Change

Add a bounded ancestry check using `lstat()` and `FILE_ATTRIBUTE_REPARSE_POINT` where available. Reject reparse-point ancestors before exclusive creation, and repeat the check after writing alongside the existing file identity/byte readback checks. Synthetic tests cover a directory reparse point that is not reported as a symlink and a reparse-point substitution during post-write verification.

## Limits

These are repeated local metadata checks, not atomic dirfd traversal or protection from a hostile kernel/concurrent filesystem writer. The authorization packet remains review-only and does not authorize payment, external compute, preflight, training, Candidate generation, protected V2 evaluation, or promotion. V3 Contract 1 and frozen V1/V2/Local UI/Launcher evidence remain unchanged.

## Validation

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed. PR #5 remains OPEN/DRAFT/UNMERGED under its existing gate.
