# ARK Run1364 — Planner COMMIT-UNKNOWN recovery and event-prefix integrity

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `884bd3df8a6966065d0861677bf50eb63db2f9a9`.
- Child branch: `research/run1364-planner-journal-commit-unknown-rebase-20261125`.
- Rebased the prior isolated Run996 regression suite. Its earlier CI/evidence does not transfer to this exact base.
- Verified current PlannerJournal source blob at the parent: `d27298a3c6ed5b9d8421ac50944b966a279c8db5`; no production Planner source change is included.
- Source/test rebase basis HEAD: `ae89c30f6e3f209f28467204c2b62f0c8b25d83e`.

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
