# V3 Run1065 — inherited-main Ruff compatibility

- Target: gated Draft PR #5, branch `research/v3-learning-evaluation`.
- Exact parent work-basis HEAD: `2ddc32a69dd32541497373ac76be2c1db332f88f` (after PR #188's free-only dangling-reparse-leaf guard).
- PR #188 child exact-head CI: run `44901609034`, GREEN 6/6.
- V3 parent-head CI: run `44905840608`, FAIL 6/6 at the shared Ruff import-order check.
- Child branch: `research/run1065-v3-mainbase-ruff-compat`.

## Finding and correction

The V3 branch's PR CI merge view inherits `tests/test_personal_context_replay_process_crash_run1033.py` from current `main`. Ruff reports I001 in that file before tests start. The V3 branch itself did not contain the file, so this child adds a branch-local copy with only the import-group separator corrected. The test body and production code are unchanged.

This does not repair or rewrite `main`, does not remove the accidental file, and does not replace the still-Draft recovery proposal PR #182. It is a reversible branch-level compatibility fix so PR #5 can be validated without changing main.

## Evidence and limits

Fresh exact-head CI is required for this child. The prior PR #188 GREEN run certifies only its exact child head and does not transfer to this fix or the PR #5 merge view. No local Ruff/pytest PASS is claimed.

PR #5 remains Draft/unmerged and V3 remains NOT_PASSED. No frozen V3 Contract, Candidate, protected V2 evaluation, real training, paid service, external compute, credentials, UI, or main branch change is involved.
