# JARVIS Run1256 — proactive-state process-exit recovery rebased

## Exact basis

- Repository: `Iam-2squared/ark-ai`.
- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `e3448745e237fa320641ad7b38a67098dfd640df`.
- Rebased test-only package from Draft PR #428, exact source child HEAD `1d0a63b6d4e2d4a8038c4975b6e4d2dcb3fa6463`.
- Test body carried forward unchanged from the exact-head-GREEN source child.
- No proactive production source, schema, policy, CAS semantics or frozen contract changes.

## Coverage

A spawned child process writes one synthetic `ELIGIBLE_PREVIEW` state through the public SQLite ledger API and exits abruptly after the transition returns. A fresh ledger verifies the durable revision, observation digest, timestamps, decision and rolling-window entry. It confirms notification, dispatch, replay and consent authority remain false; scans the database and surviving SQLite WAL/SHM sidecars for raw synthetic observation text; rejects stale CAS without changing the recovered snapshot; and accepts an explicit CAS from the recovered revision without creating another preview.

## Evidence boundary

The source child CI [45322042127](https://github.com/Iam-2squared/ark-ai/actions/runs/45322042127) was GREEN 6/6 on its older parent. That result does not certify this rebased child. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no local pytest/Ruff PASS is claimed.

This verifies process-exit recovery after a successful API return. It does not inject a crash inside native SQLite COMMIT, prove fsync/power-loss durability, establish a trusted clock, authorize timers/notifications, or permit external actions. All data is synthetic and stored only in disposable local SQLite.

No paid/external compute, Candidate generation/promotion, protected V2 evaluation, credentials, hardware, UI/frontend work, destructive action, frozen-contract change or main merge. PR #5/#8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
