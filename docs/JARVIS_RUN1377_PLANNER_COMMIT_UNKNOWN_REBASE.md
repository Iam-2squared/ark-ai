# ARK Run1377 — Planner COMMIT-UNKNOWN recovery and event-prefix integrity

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `e212e77cb3432e0e226cebd4b9c1f2836eb064bc`.
- Verified production source blob: `src/ark/agency/planner_journal.py` at `d27298a3c6ed5b9d8421ac50944b966a279c8db5`; the source is unchanged by this test-only rebase.
- Child branch: `research/run1377-planner-commit-unknown-latest-20261125`.
- Rebased from Draft PR #543 / Run1364. Its exact-head CI run `45546570051` was GREEN on the older parent only and does not transfer to this branch.

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

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No PASS is claimed before that run completes. PR #5 and PR #8 remain Draft/unmerged; PR #9 remains untouched. No paid compute, Candidate, protected V2 evaluation, credentials, hardware, destructive action, UI/frontend work, or main merge.
