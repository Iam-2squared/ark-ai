# Run1210 — proactive-state process-exit recovery on latest foundation

## Exact basis

- Repository: `Iam-2squared/ark-ai`.
- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent work-basis HEAD at branch creation: `5059b08222c309c173c17dcb8e246dd9599be7a4`.
- Rebased test-only package from Draft PR #359 exact child HEAD: `520ada9c4e8240fd5ab909b06dccaed78c895da0`.
- Earlier source PR #344 exact head: `5b33d959e67c1fcebeaa7107d0da2324bfbc8c68`.
- Prior exact-head CI [45150853763](https://github.com/Iam-2squared/ark-ai/actions/runs/45150853763) was GREEN on PR #359's child head only; it does not transfer to this rebase.
- New child branch: `research/run1210-proactive-state-process-crash-latest`.

## Coverage

A spawned child process writes one synthetic `ELIGIBLE_PREVIEW` state through the public SQLite ledger API and exits abruptly after the transition returns. A fresh parent-side ledger verifies the durable revision, observation digest, timestamps, decision and rolling-window entry. It confirms notification, dispatch, replay and consent authority remain false; scans the database and any surviving SQLite WAL/SHM sidecars for raw synthetic observation text; rejects a stale CAS revision without changing the recovered snapshot; and accepts an explicit CAS from the recovered revision without creating another preview.

## Compatibility review

- `src/ark/proactive_state_ledger.py` is byte-identical between the earlier parent and the current PR #8 work-basis (blob `95b4c001ed131ed1924c65a362fec770b8392fa2`).
- This child adds only the process-exit regression and its evidence note; it does not modify the proactive ledger, schema, policy, CAS semantics, or denial-only authority properties.

## Evidence boundary

This verifies process-exit recovery after a successful API return. It does not inject a crash inside native SQLite COMMIT, prove fsync/power-loss durability, establish a trusted clock, authorize timers/notifications, or permit external actions. All data is synthetic and stored only in disposable local SQLite.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed. No paid/external compute, Candidate generation/promotion, protected V2 evaluation, credentials, hardware, UI/frontend work, frozen-contract change, destructive operation, or main merge. PR #5/#8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
