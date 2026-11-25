# JARVIS Run1272 — proactive-state process-exit recovery rebased

## Exact basis

- Repository: `Iam-2squared/ark-ai`.
- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `993fbcb3efb69c4c818327aefb8e3d40ea9d673e`.
- Rebased test-only package from Draft PR #438, whose prior child head was `db0e9c45a7e1188a0458997c99875445278f6210` on older base `e3448745e237fa320641ad7b38a67098dfd640df`.
- The test body is carried forward unchanged apart from its run label; no proactive production source, schema, policy, CAS semantics or frozen contract changes.

## Coverage

A spawned child process writes one synthetic `ELIGIBLE_PREVIEW` state through the public SQLite ledger API and exits abruptly after the transition returns. A fresh ledger verifies the durable revision, observation digest, timestamps, decision and rolling-window entry. It confirms notification, dispatch, replay and consent authority remain false; scans the database and surviving SQLite WAL/SHM sidecars for raw synthetic observation text; rejects stale CAS without changing the recovered snapshot; and accepts an explicit CAS from the recovered revision without creating another preview.

## Evidence boundary

Prior PR #438 CI [45342964751](https://github.com/Iam-2squared/ark-ai/actions/runs/45342964751) was GREEN 6/6 on its older parent only. It does not certify this rebase. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no local pytest/Ruff PASS is claimed.

This verifies process-exit recovery after a successful API return. It does not inject a crash inside native SQLite COMMIT, prove fsync/power-loss durability, establish a trusted clock, authorize timers/notifications, or permit external actions. All data is synthetic and stored only in disposable local SQLite.

No paid/external compute, Candidate generation/promotion, protected V2 evaluation, credentials, hardware, UI/frontend work, destructive action, frozen-contract change or main merge. PR #5/#8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
