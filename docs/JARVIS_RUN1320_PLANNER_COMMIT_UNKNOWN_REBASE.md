# ARK Run1320 — Planner COMMIT-UNKNOWN recovery regressions rebased

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD after Run1317 Memory ingress integration: `77d3b2f50d258bb3694afc0d03830e0d44644961`.
- Child branch: `research/run1320-planner-commit-unknown-rebase-20261125`.
- Rebased the regression package from Draft PR #495 / Run1314. Its prior exact-head CI [45453163788](https://github.com/Iam-2squared/ark-ai/actions/runs/45453163788) was GREEN 6/6 on the old parent only; it does not transfer to this rebase.
- PlannerJournal production source remains unchanged at the new parent.

## Regression coverage

- Simulate loss of the SQLite COMMIT acknowledgement after native COMMIT succeeds for both genesis creation and a step transition.
- Require explicit `PlannerJournalCommitUnknown` rather than a blind retry.
- Cold-recover the durable genesis/transition; reject duplicate genesis and stale pre-COMMIT graph/sequence reuse.
- Keep recovered `RUNNING` work ambiguous, not ready, and without automatic replay or dispatch authority.
- Reject interior and tail event-prefix truncation when metadata still claims the longer frontier.

The fixture tests acknowledgement loss after SQLite reports COMMIT success. It does not claim rollback or power-loss durability.

## Scope and evidence boundary

Test/documentation-only. No Planner source, schema, DDL, transition policy, CAS semantics, public API or frozen contract changes. Synthetic ToolCalls and disposable local SQLite only; no ToolBackend dispatch, live data, external service, trusted clock, consent or exactly-once external-effect claim.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. PR #5/#8 remain Draft/unmerged; PR #9 remains untouched. No paid/external compute, Candidate, protected V2 evaluation, credentials, hardware, destructive action, UI/frontend work or main merge.
