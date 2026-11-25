# Run1264 — repair the V3 merge-ref Ruff import-order failure

## Exact basis

- Parent: Draft PR #5, branch `research/v3-learning-evaluation`.
- Exact parent work-basis HEAD: `505b3d0e4af55cd67e4bf0d26e5462cfff999815`.
- The failing exact-head CI run is [45336581295](https://github.com/Iam-2squared/ark-ai/actions/runs/45336581295).

## Change

The parent merge-ref Ruff run reported one I001 import-order error in
`tests/test_personal_context_replay_process_crash_run1033.py`. The test body,
fixtures, replay-ledger behavior, and assertions are unchanged. The single
blank line between `import pytest` and the `ark` imports is removed to match
the repository's current Ruff/isort classification.

The file exists on the current `main` base but was absent from the older PR #5
branch snapshot; this child adds the corrected byte content to PR #5's branch
without writing to `main`. No lint rule is disabled, no file is excluded, and
no test is weakened or deleted.

## Evidence boundary

This is a formatting-only CI repair. It does not change Personal Context
runtime behavior, replay policy, privacy semantics, V3 Contract 1, or the
execution snapshot. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is
required; the previous parent run remains FAIL.

No paid/external compute, model weights, Candidate generation/promotion,
protected V2 evaluation, credentials, hardware, destructive operation,
frozen-contract change, UI/frontend work, or main merge. PR #5 remains
Draft/unmerged. PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
