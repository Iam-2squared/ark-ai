# Run1103 — V3 authorization packet stat-predicate custody

## Exact basis

- Parent: gated Draft PR #5, `research/v3-learning-evaluation`
- Work-basis HEAD: `2ddc32a69dd32541497373ac76be2c1db332f88f`
- Child branch: `research/run1103-v3-auth-stat-predicate-custody`
- Source: `src/ark/learning/authorization.py`
- Tests: `tests/v3/test_authorization_packet_stat_predicate_custody_run1103.py`

## Change

- Pin the import-original `stat` module, `S_ISLNK` predicate and `S_ISREG` predicate.
- Reject module or predicate replacement before filesystem metadata is read.
- Use the retained original predicates for symlink/reparse and regular-file classification.
- Recheck the policy at the start of ancestor review and before any packet-writer path metadata operation.
- Add synthetic regressions for module replacement, each predicate replacement, and writer ordering before `lstat`.

## Safety boundary

This hardens local review-packet path classification only. It does not make pathname checks atomic against a hostile concurrent filesystem writer, authorize external compute, start training, create a Candidate, open validation or historical V2, or authorize promotion/main merge. PR #5 remains Draft/unmerged; no GPU, paid API/service, credential or account connection was used.

## Validation

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed.
