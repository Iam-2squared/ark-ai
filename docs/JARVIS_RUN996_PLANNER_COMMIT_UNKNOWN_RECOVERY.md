# Run996 — Planner COMMIT-UNKNOWN recovery and event-prefix truncation

**Work basis:** Draft PR #19 exact head `c08c7e9e6c836285362da96663dee903479da98a`, whose exact-head CI run [#44549000547](https://github.com/Iam-2squared/ark-ai/actions/runs/44549000547) completed GREEN across all six Windows/Ubuntu × Python 3.11–3.13 jobs.

**Isolated branch:** `research/planner-journal-commit-unknown-run996`, based on PR #19. PRs #18 and #19 remain Draft/unmerged.

## New regression coverage

- Simulate a SQLite `COMMIT` that durably succeeds but whose acknowledgement is lost before the caller receives it.
- Exercise both Planner genesis creation and a step transition. Each path must raise `PlannerJournalCommitUnknown`, not return success or claim rollback.
- Reopen the journal and recover the durable genesis/transition from SQLite.
- Prove a second genesis creation conflicts with the already-persisted plan.
- Prove the pre-commit graph/sequence cannot be reused after an uncertain transition. A recovered `RUNNING` step remains explicitly ambiguous, is not ready, and does not grant automatic replay or dispatch authority.
- Delete an interior event and, separately, the tail event from synthetic journals. Recovery must reject both a broken sequence prefix and a metadata frontier that extends beyond retained rows.

The fault fixture commits through the real SQLite connection and raises only after the underlying `COMMIT` returns. This tests a lost response, not a simulated rollback.

## Safety and limits

Only disposable local SQLite files and synthetic ToolCalls are used. No backend is invoked; no Planner schema, DDL, transition policy, CAS rule, recovery semantics, frozen contract, Memory source, V2/V3 evidence, UI branch, or main branch is modified. The tests establish local journal recovery behavior only; they do not provide authenticated storage, anti-rollback protection, trusted time, consent, or external-effect proof.

**Validation:** regression tests and this report are saved. Exact-head CI has not yet been run for this branch; no PASS is claimed. No local pytest or physical-machine result is claimed.
