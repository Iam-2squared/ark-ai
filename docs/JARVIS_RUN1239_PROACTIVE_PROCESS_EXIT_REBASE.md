# JARVIS Run1239 — proactive-state process-exit recovery on latest foundation

## Exact basis

- Repository: `Iam-2squared/ark-ai`.
- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `ec91026bae7ae12b7fad924cc2971c5c8c74f351`.
- Reapplies the test-only process-exit regression from Draft PR #416, exact predecessor head `6800428b11bd04ac0cb3e298028ba863a72df08f`.
- Predecessor exact-head CI [45291879975](https://github.com/Iam-2squared/ark-ai/actions/runs/45291879975) was GREEN on its older base; it does not transfer to this rebase.
- New child branch: `research/run1239-proactive-process-exit-rebase`.

## Coverage

A spawned child process writes one synthetic `ELIGIBLE_PREVIEW` state through the public SQLite ledger API and exits abruptly after the transition returns. A fresh parent-side ledger verifies the durable revision, observation digest, timestamps, decision and rolling-window entry. It confirms notification, dispatch, replay and consent authority remain false; scans the database and any surviving SQLite WAL/SHM sidecars for raw synthetic observation text; rejects a stale CAS revision without changing the recovered snapshot; and accepts an explicit CAS from the recovered revision without creating another preview.

## Compatibility

The package adds only a process-exit regression and this evidence note. It does not modify the proactive ledger, schema, policy, CAS semantics or denial-only authority properties. The parent contains the Planner genesis COMMIT-UNKNOWN regression and the Unicode privacy identity rebase; this child changes neither component.

## Evidence boundary

This verifies process-exit recovery after a successful API return. It does not inject a crash inside native SQLite COMMIT, prove fsync/power-loss durability, establish a trusted clock, authorize timers/notifications, or permit external actions. All data is synthetic and stored only in disposable local SQLite.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed. No paid/external compute, Candidate generation/promotion, protected V2 evaluation, credentials, hardware, UI/frontend work, frozen-contract change, destructive operation or main merge. PR #5/#8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
