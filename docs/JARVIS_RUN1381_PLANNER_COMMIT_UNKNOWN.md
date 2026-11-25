# Run1381 — Planner COMMIT-UNKNOWN recovery and event-prefix integrity

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `11d72bef1b69df06ed0c0102d6154fc4d44a0214`.
- Child PR: Draft #560, branch `research/run1381-planner-commit-unknown-rebase-20261125`.
- Child test commit before this evidence document: `9213906cc30a5bbc2bc2cc7a2866e671b7e95ae7`.
- Verified PlannerJournal source blob on the parent: `d27298a3c6ed5b9d8421ac50944b966a279c8db5`; no production source change is included.
- Rebased the isolated Run1364 test package; its earlier CI does not transfer to this exact child head.

## Regression coverage

- Inject a lost SQLite COMMIT acknowledgement after the underlying native COMMIT succeeds.
- Exercise genesis creation and a step transition; both must raise `PlannerJournalCommitUnknown`.
- Reopen and recover the durable genesis/transition rather than retrying.
- Reject a second genesis creation and stale pre-COMMIT graph/sequence reuse.
- Keep recovered `RUNNING` work ambiguous, not ready, and without automatic replay or dispatch authority.
- Reject interior and tail event-prefix truncation when metadata still claims the longer frontier.

The fixture raises only after the real SQLite connection reports COMMIT success. It tests acknowledgement loss, not rollback or power-loss durability.

## Scope and evidence boundary

Test/documentation-only. No Planner source, schema, DDL, transition policy, CAS semantics, public API, or frozen contract changes. Synthetic ToolCalls and disposable local SQLite only; no ToolBackend dispatch, live data, external service, trusted clock, consent, or exactly-once external-effect claim.

Exact-head CI run `45575572631` was queued when this document was written. Fresh Windows/Linux × Python 3.11–3.13 CI is required; no PASS is claimed before it completes. No local pytest/Ruff PASS is claimed. PR #5/#8/#9 remain Draft/unmerged; no paid compute, Candidate, protected V2 evaluation, credentials, hardware, destructive action, main merge or UI/frontend work occurred. ARK/JARVIS remains NOT_PASSED.
