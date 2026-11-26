# Run1159 — proactive state process-crash recovery rebase

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent HEAD at child creation: `aa466abdf3de9abc9d1560e614952596c7cc8b19`.
- Source test package: Draft PR #304, `research/run1120-proactive-state-process-crash`, exact child HEAD `c082c2dfd0004a7d3525dbfbda9556a7a9bc53e8`.
- Source exact-head CI run [45059948886](https://github.com/Iam-2squared/ark-ai/actions/runs/45059948886) was GREEN on the source head only; it does not transfer to this rebase.
- New branch: `research/run1159-proactive-state-crash-rebase`.

## Coverage

A spawned child process writes one synthetic `ELIGIBLE_PREVIEW` state through the public SQLite ledger API and exits abruptly after the transition returns. A fresh parent-side ledger then verifies the durable revision, observation digest, timestamps, decision and rolling-window entry; confirms notification, dispatch, replay and consent authority remain false; scans the database and any SQLite WAL/SHM sidecars for raw synthetic observation text; rejects a stale CAS revision without changing the recovered snapshot; and accepts an explicit CAS from the recovered revision without creating another preview.

## Evidence boundary

This verifies process-exit recovery after a successful API return. It does **not** inject a crash inside native SQLite COMMIT, prove fsync/power-loss durability, establish a trusted clock, authorize timers/notifications, or permit external actions. The production ledger, schema, policy, CAS semantics and denial-only behavior are unchanged.

All data is synthetic and stored only in disposable local SQLite. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No paid/external compute, Candidate, protected V2 evaluation, credentials, hardware, UI/frontend work, frozen-contract change, destructive operation, or main merge is involved. PR #5 and #8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
