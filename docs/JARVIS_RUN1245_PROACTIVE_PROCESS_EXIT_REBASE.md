# JARVIS Run1245 — proactive-state process-exit recovery rebased

## Exact basis

- Repository: `Iam-2squared/ark-ai`.
- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `609a3cdaf7ad3b08ef90f2398378d9984bdc329d`.
- Rebased test-only package from Draft PR #422, source child HEAD `df26a5ffe02d65d629b8626119cdbf8fc99b8525`.
- The test body is carried forward unchanged; no proactive production source, schema, policy, CAS semantics or frozen contract changes.
- Previous child CI [45309461059](https://github.com/Iam-2squared/ark-ai/actions/runs/45309461059) was GREEN 6/6 on the older parent and does not certify this rebased head. Fresh exact-head CI is required.

## Coverage

A spawned child process writes one synthetic `ELIGIBLE_PREVIEW` state through the public SQLite ledger API and exits abruptly after the transition returns. A fresh ledger verifies the durable revision, observation digest, timestamps, decision and rolling-window entry. It confirms notification, dispatch, replay and consent authority remain false; scans the database and surviving SQLite WAL/SHM sidecars for raw synthetic observation text; rejects stale CAS without changing the recovered snapshot; and accepts an explicit CAS from the recovered revision without creating another preview.

## Evidence boundary

This verifies process-exit recovery after a successful API return. It does not inject a crash inside native SQLite COMMIT, prove fsync/power-loss durability, establish a trusted clock, authorize timers/notifications, or permit external actions. All data is synthetic and stored only in disposable local SQLite.

No paid/external compute, Candidate generation/promotion, protected V2 evaluation, credentials, hardware, UI/frontend work, destructive action, frozen-contract change or main merge. PR #5/#8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no local pytest/Ruff PASS is claimed.
