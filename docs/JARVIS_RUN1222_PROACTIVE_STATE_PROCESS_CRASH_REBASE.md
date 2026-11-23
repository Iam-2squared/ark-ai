# Run1222 — proactive-state process-exit recovery on current foundation

## Exact basis

- Repository: `Iam-2squared/ark-ai`.
- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `ef021d9f75de06078674d6b4ba6c31dfce1f2b33`.
- Rebased test-only source: Draft PR #401, `research/run1217-proactive-state-process-crash-rebase`, exact child HEAD `e68a5e3dd053c8493ecf89586b857a0ca3c0dc80`.
- Source predecessor exact-head CI [45263231802](https://github.com/Iam-2squared/ark-ai/actions/runs/45263231802) was GREEN 6/6 on the predecessor child only; it does not transfer to this rebase.
- New child branch: `research/run1222-proactive-state-process-crash-latest`.

## Coverage

A spawned child process writes one synthetic `ELIGIBLE_PREVIEW` state through the public SQLite ledger API and exits abruptly after the transition returns. A fresh parent-side ledger verifies the durable revision, observation digest, timestamps, decision and rolling-window entry. It confirms notification, dispatch, replay and consent authority remain false; scans the database and any surviving SQLite WAL/SHM sidecars for raw synthetic observation text; rejects a stale CAS revision without changing the recovered snapshot; and accepts an explicit CAS from the recovered revision without creating another preview.

## Compatibility

The package adds only a process-exit regression and this evidence note. It does not modify the proactive ledger, schema, policy, CAS semantics or denial-only authority properties. The parent contains the Planner durable journal and the Memory WAL delete/recreate ABA regression; this child changes neither component.

## Evidence boundary

This verifies process-exit recovery after a successful API return. It does not inject a crash inside native SQLite COMMIT, prove fsync/power-loss durability, establish a trusted clock, authorize timers/notifications, or permit external actions. All data is synthetic and stored only in disposable local SQLite.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed. No paid/external compute, Candidate generation/promotion, protected V2 evaluation, credentials, hardware, UI/frontend work, frozen-contract change, destructive operation, or main merge. PR #5/#8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
