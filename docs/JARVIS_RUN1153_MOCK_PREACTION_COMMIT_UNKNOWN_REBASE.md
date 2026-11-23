# Run1153 — Mock executor pre-action audit COMMIT ambiguity rebase

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Parent HEAD at branch creation: `45fc595cc78e855ed726e32fae8f4eddd38e291a`.
- Source test PR #333 exact head: `8a0d9d4bc91b6bcea3c373d53f470d7756123a86`.
- Source exact-head CI: [45107744522](https://github.com/Iam-2squared/ark-ai/actions/runs/45107744522), GREEN 6/6 on the source head only.
- Child branch: `research/run1153-mock-preaction-commit-unknown-rebase`.
- Test file: `tests/test_disconnected_mock_executor_preaction_commit_unknown_run1153.py`.
- Test commit: `25e92590f7b4e1d651cd34b3efac2f3446e7d10f`.

## Change

Reapplies the synthetic disconnected mock-executor regression for both possible outcomes of a lost pre-action ActionAudit COMMIT acknowledgement:

- Native COMMIT followed by lost acknowledgement: cold audit readback contains exactly the pre-action event.
- Native rollback followed by lost acknowledgement: cold audit readback contains no pre-action event.

In both cases the occurrence reservation remains durable, the mock backend is never called, and a fresh process-local PermissionGate cannot replay the same token with a different occurrence ID. The subprocess installs the stable SQLite connection factory before ARK imports, preserving import-original dependency guards.

This is test-only. Production executor, ActionAudit, occurrence store, ToolRegistry, PermissionGate, and all schemas/contracts are unchanged.

## Validation boundary

The source PR #333 exact-head CI result is historical and does not transfer to this rebase. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no PASS is claimed until that run completes.

Synthetic local SQLite and an inert in-process mock only. No fsync/power-loss durability, cross-store atomicity, trusted time, authenticated consent, independent storage custody, real backend dispatch, or exactly-once external effect is established. No automatic retry or replay is added.

No paid/external compute, Candidate, protected V2 evaluation, credentials, physical hardware, UI/frontend work, frozen-contract change, destructive operation, or main merge. PR #5 and PR #8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
