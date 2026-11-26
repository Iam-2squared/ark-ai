# ARK AI Run759 — Non-UI WAL abort / detached READ race / audit crash barriers

**Scope:** FREE-ONLY, disconnected, reversible local SQLite tests on Draft PR #8. No product/UI changes, no live tool/backend, physical hardware, payment, model training, Candidate or frozen evaluation. No PR merge. The tests deliberately assert evidence limitations rather than treating a synthetic receipt as approval.

## Verified starting basis

- **Work-basis HEAD:** `fcc5424bc4760e1c3a895200cb03bd498da5bba4` (Run758 canonical checkpoint, `research/jarvis-foundations`).
- **Independent historical CI:** [#42771930045](https://github.com/Iam-2squared/ark-ai/actions/runs/42771930045) is **COMPLETED SUCCESS, 6/6** for that **old exact HEAD**, Windows/Ubuntu × Python 3.11/3.12/3.13. GitHub's six job records each say completed/success. This is NOT CI proof for Run759.
- **Normal Github Contents API source/test commit sequence:** Memory `d991677b1775322220ca0d3eef77454e7d084fce` → READ journal `20387061f26f28c4948f03c6cc43f9bc2d78e2b5` → action audit `e1d5cb8c7936101b67acd7892373e35a3eb3406c`. All three are **test-only** changes.
- **Static inspection:** fetched all three authored test files back from their saved exact branch, confirmed file existence, exact blob SHA and no lines above 99 characters. This is **NOT** Ruff/pytest; cross-platform CI is separately required.

## A. Memory partial transaction crash — 4 new cases

`tests/test_memory_partial_wal_process_abort_run759.py`

A spawned interpreter starts `BEGIN IMMEDIATE`, stages either a Memory row update alone, event insertion alone, row-then-event, or event-then-row, and exits via `os._exit(0)` **without COMMIT or handler unwinding**. After an independent reopen, tests require (i) identical persisted row/revision and full event list; (ii) retained coherent row/event/prefix witnesses still report `UNCHANGED_LOCAL_HISTORY`; (iii) the original retained generation remains usable by a deliberate, later manual CAS update; (iv) no action/authentication/cross-store rights are invented. Unlike the preceding Run758 row+event WAL test, these fixtures cover *half-staged* local SQL and both staging orders. They do not model power loss, authenticated filesystem provenance or external effects.

## B. Planner disconnected READ journal multiprocess CAS — 2 new cases

`tests/test_read_journal_multiprocess_cas_run759.py`

Two independently spawned interpreters open the same marked journal and wait on a shared process event before both try to append under exactly the same caller-retained `ReadJournalWitness`. Test variants use the same receipt identity or distinct identities. Exactly one durable append must win, the other must reject a stale witness; after cold reopen, the complete receipt tuple must match the winning witness, while the old witness is refused. All witness and snapshot authority flags remain `False`. No READ ToolBackend is invoked. This is a **local ledger CAS** proof, not Planner/Tool execution, signed custody or permission to replay.

## C. ActionAudit lost response and partial WAL stages — 4 new cases

`tests/test_action_audit_process_crash_boundaries_run759.py`

A separate process performs one of three uncommitted SQL changes (deletes the first audit event, alters its outcome, or stages another row) and terminates without COMMIT. A cold audit reader must see the original dense history, and a later proper audit append must produce ID 2. A fourth case deliberately **commits** a valid audit record and exits before reporting its receipt; manual readback must observe the committed event without a second append. Raw private ToolCall arguments must not appear in the SQLite main database bytes. A successful local audit row is **not** evidence of an external side effect or user consent. In particular, an unknown external WRITE must never be automatically retried.

## D. Proactive scheduler cold-start clock/interval fence — 3 new cases

`tests/test_proactive_cold_clock_interval_run759.py`, ordinary Contents API test commit `ede7b90e42cf231579c046d459de55fa9823332b`.

A second, distinct Python interpreter opens the content-minimized synthetic proactive ledger following one committed preparation at time 100. With the same scope/policy but a different observation digest, time **99** must reject the persisted clock rollback, **104** must reject the five-millisecond minimum interval and boundary time **105** may admit exactly one second inert preparation. New cold opens must retain a count of 1/1/2 respectively. Neither receipt grants a notification, ToolBackend dispatch, replay, authenticated time or consent. Authored file fetched back from exact branch: no source line over 99 characters. New exact test-head CI [#42778247010](https://github.com/Iam-2squared/ark-ai/actions/runs/42778247010) was QUEUED at sampling. It is **not** an all-platform PASS claim.

**Total new parametrized Run759 tests: 13** across four non-UI packages (Memory 4 + READ journal 2 + ActionAudit 4 + Proactive 3). Existing production source and frozen contracts are unchanged. The earlier three-lane CI samples below remain historical samples for those exact older SHAs; each new commit has separate CI evidence.

## CI pipeline and failure policy

- New source/test-head runs at status sampling: [#42777588388](https://github.com/Iam-2squared/ark-ai/actions/runs/42777588388) (Memory) **IN PROGRESS**; [#42777652288](https://github.com/Iam-2squared/ark-ai/actions/runs/42777652288) (+READ) **IN PROGRESS**; [#42777818544](https://github.com/Iam-2squared/ark-ai/actions/runs/42777818544) (+audit) **QUEUED**. Each is a distinct SHA. No equivalent manual workflow re-run/dispatch was requested.
- If any job FAILS, analyze its exact job log; correct the smallest source/test error via ordinary permitted Contents API. Do not assign an earlier successful CI run to a newer HEAD; a separate report/checkpoint commit also has its own HEAD.
- FROZEN/APPROVAL: main, V1/V2/Local UI/Launcher evaluation/contracts, protected V2 final gate, V3 Draft PR #5 and paused UI Draft PR #9 remain unchanged. User authorization is still required for spending, credentials/accounts, Candidate/weights or promotion, irreversible privacy actions, physical PC access, frozen changes and protected main merge.

## Cross-ledger threat model / integration limitations

MemoryStore, detached READ journal, ActionAudit and synthetic occurrence reservation each have **different SQLite transactions**. Even if all four have green CAS/WAL tests individually, the collection does not have a shared atomic commit, verified external signer, trusted clock, authorized identity, independent audit custody or exactly-once external effect proof. Crash windows between *audit committed / occurrence not committed*, *occurrence reserved / audit not committed*, or *audit committed / external result unknown* remain authority blockers. The only allowed result from disconnected inspectors is **deny/quarantine/mock**, not actual dispatch. Future integration must specify a single durable boundary or explicit recovery protocol, authenticated consent and external idempotency before any real ToolBackend action.

## Next plan / 今後の方針

1. Confirm exact-head six-platform CI for all three source/test commits; repair any real failures without weakening guards.
2. Extend independently retained Memory coherent witnesses around COMMIT-UNKNOWN and WAL snapshots, and READ journal crash/restart test evidence only after predecessor CI is green.
3. Design restart-safe registry-bound PermissionGate → audit-before-action → occurrence token → disconnected mock-only Executor bridge; keep unknown WRITE quarantined. Do not infer cross-store atomicity.
4. Preserve all UI/frozen/V3 gates; continue privacy/retention and proactive/Observation backend review on independent free-only lanes. Overall ARK/JARVIS/V3: **NOT_PASSED**.
