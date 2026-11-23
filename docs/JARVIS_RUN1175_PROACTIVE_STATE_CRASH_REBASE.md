# Run1175 — Run1175: proactive eligibility state survives a real process exit

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent HEAD at branch creation: `107b56849fec47e4d2e24576958b358c0aef697b`.
- Rebased the test-only package from Draft PR #353 exact child HEAD `dc372a993b6bde5561fbca717409e9622f2a7246`.
- Source package: Draft PR #344 exact head `5b33d959e67c1fcebeaa7107d0da2324bfbc8c68`.
- Source exact-head CI [45141812771](https://github.com/Iam-2squared/ark-ai/actions/runs/45141812771) was GREEN on the prior child head only; it does not transfer to this rebase.
- New branch: `research/run1175-proactive-state-crash-rebase`.

## Coverage

A spawned child process writes one synthetic ELIGIBLE_PREVIEW state through the public SQLite ledger API and exits abruptly after the transition returns. A fresh parent-side ledger verifies the durable revision, observation digest, timestamps, decision and rolling-window entry; confirms notification, dispatch, replay and consent authority remain false; scans the database and any SQLite WAL/SHM sidecars for raw synthetic observation text; rejects a stale CAS revision without changing the recovered snapshot; and accepts an explicit CAS from the recovered revision without creating another preview.

## Evidence boundary

This verifies process-exit recovery after a successful API return. It does not inject a crash inside native SQLite COMMIT, prove fsync/power-loss durability, establish a trusted clock, authorize timers/notifications, or permit external actions. Production proactive ledger, schema, policy, CAS semantics and denial-only behavior are unchanged. All data is synthetic and stored only in disposable local SQLite.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No paid/external compute, Candidate generation/promotion, protected V2 evaluation, credentials, hardware, UI/frontend work, frozen-contract change, destructive operation, or main merge. PR #5 and #8 remain Draft/unmerged; PR #9 remains untouched; ARK/JARVIS remains NOT_PASSED.
