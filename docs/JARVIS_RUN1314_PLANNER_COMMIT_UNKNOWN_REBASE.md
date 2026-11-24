# ARK Run1314 — Planner COMMIT-UNKNOWN recovery and event-prefix integrity

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `824bb987f0addf4e961c9f4949f6075ca42a1caa`.
- Child branch: `research/run1314-planner-commit-unknown-rebase-20261125`.
- Rebased the prior isolated Run1310 regression suite. Its exact-head CI [45441811126](https://github.com/Iam-2squared/ark-ai/actions/runs/45441811126) was GREEN on the old child only and does not transfer to this base.
- Verified PlannerJournal source blob at the parent: `173ff97214032bc781f104ce680354b3fa0b0dad`; no production Planner source change is included.

## Regression coverage

- Inject a lost SQLite COMMIT acknowledgement after the underlying native COMMIT succeeds.
- Exercise both genesis creation and a step transition; both must raise `PlannerJournalCommitUnknown`.
- Reopen and recover the durable genesis/transition rather than retrying.
- Reject a second genesis creation and stale pre-COMMIT graph/sequence reuse.
- Keep recovered `RUNNING` work ambiguous, not ready, and without automatic replay or dispatch authority.
- Reject interior and tail event-prefix truncation when metadata still claims the longer frontier.

The fixture raises only after the real SQLite connection reports COMMIT success. It tests acknowledgement loss, not rollback or power-loss durability.

## Scope and evidence boundary

Test/documentation-only. No Planner source, schema, DDL, transition policy, CAS semantics, public API, or frozen contract changes. Synthetic ToolCalls and disposable local SQLite only; no ToolBackend dispatch, live data, external service, trusted clock, consent, or exactly-once external-effect claim.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No PASS is claimed before that run completes. PR #5/#8 remain Draft/unmerged; PR #9 remains untouched. No paid compute, Candidate, protected V2 evaluation, credentials, hardware, destructive action, UI/frontend work, or main merge.
