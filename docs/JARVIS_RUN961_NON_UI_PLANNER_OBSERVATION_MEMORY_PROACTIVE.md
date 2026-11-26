# ARK AI Run961 — non-UI Planner, Observation, Memory and Proactive safeguards

**Work basis (Run960 canonical checkpoint):** `7202dbf9fa44d76edb15a1fd0fa9956cc264c95c`. Prior exact-HEAD CI [#44248379342](https://github.com/Iam-2squared/ark-ai/actions/runs/44248379342) completed **SUCCESS 6/6** on Windows/Ubuntu × Python 3.11–3.13. This is evidence for Run960 only, **not** this new work. Branch `research/jarvis-foundations`, Draft PR #8; no main merge.

## NEW work — four distinct non-UI work packages, 58 authored param cases

1. **Planner opt-in graph identity admission.** Commit [`dfbca5fe`](https://github.com/Iam-2squared/ark-ai/commit/dfbca5fec696706a3abb51cf45f5c9acb4d00aff) rejects ASCII C0 and DEL characters in step/dependency/tool/capability/scope labels prior to DAG construction, action request hashing or journal persistence. Prior NUL error classification preserved. This does **not** change frozen `PlanStep` or `ToolCall` constructors. Commit [`9df050ab`](https://github.com/Iam-2squared/ark-ai/commit/9df050ab8d22044783e8d20ebed3137af3e2435b) supplies 33 cases for raw, reflected and legitimate Unicode labels. No tool dispatch.
2. **Disconnected synthetic Observation fixture metadata.** Commit [`12c61d26`](https://github.com/Iam-2squared/ark-ai/commit/12c61d268d89c839401ae064c8d93bad8f2cd9dc) rejects C0/DEL in fixture source and privacy labels before private-payload hashing or envelope construction, without changing frozen `ObservationEnvelope` v1. Commit [`afabbb71`](https://github.com/Iam-2squared/ark-ai/commit/afabbb719089a6ab78e91297c94332365d75ee1b) adds 13 cases including direct frozen-v1 compatibility and Unicode fixture preservation. No real media capture.
3. **Memory generation CAS, foreign-scope isolation.** Commit [`b9fa5a96`](https://github.com/Iam-2squared/ark-ai/commit/b9fa5a96bcef40b1c45b0699b7d0a9601fe0fb39) adds 8 cases: different owner/namespace × identical/changed foreign replacement × read-only/readwrite pinned WAL reader. Deleting/recreating a foreign lifetime must deny the stale foreign token without invalidating an unchanged primary lifetime; exact global event chronology and cold reads checked.
4. **Proactive expired occurrence ledger after abrupt exit.** Commit [`c8f4928f`](https://github.com/Iam-2squared/ark-ai/commit/c8f4928f834d1aa4ec4d4b6b761dba879a566b63) adds 4 cases: process exits before/after a local quarantine commit × PASSIVE/TRUNCATE WAL checkpoint. On restart stale witnesses are not retry authority; local reconstructions are explicitly **not** independently retained evidence. No timer, notification or executor starts.

The two source changes are restricted to reversible, opt-in non-frozen admission boundaries. No V1/V2/Local UI/Launcher, Observation-v1, V3 Contract 1, human-review or evaluation gates were changed. Neither hashing nor a SQLite receipt proves consent, trusted time, independent provenance, or exactly-once external effects.

## CI snapshot at package completion (NOT final HEAD GREEN)

- Prior Run960 checkpoint `7202dbf9`: [#44248379342](https://github.com/Iam-2squared/ark-ai/actions/runs/44248379342) **COMPLETED GREEN 6/6**.
- Planner source+tests `9df050ab`: [#44253723971](https://github.com/Iam-2squared/ark-ai/actions/runs/44253723971), **IN PROGRESS** (6 jobs in progress at sample).
- Observation source+tests `afabbb71`: [#44253839391](https://github.com/Iam-2squared/ark-ai/actions/runs/44253839391), **IN PROGRESS / QUEUED** (2 running, 4 queued).
- Memory `b9fa5a96`: [#44253954517](https://github.com/Iam-2squared/ark-ai/actions/runs/44253954517), **QUEUED** (6 jobs queued).
- Proactive `c8f4928f`: [#44254135498](https://github.com/Iam-2squared/ark-ai/actions/runs/44254135498), **QUEUED** (6 jobs queued).

These cases were **authored**, not reported as fully passed. Exact-head 6/6 CI for the final checkpoint must be separately established; no local full pytest and no manual workflow dispatch took place.

## Constraints and next plan

- **FREE-ONLY:** no external GPU, API, subscriptions, payments or additional credentials. No real Candidate generation/training/promotion, protected final V2 evaluation, physical-PC work, tool dispatch, destructive action, raw-Git write bypass, main merge or frozen-evidence update.
- PR #5 and paused UI PR #9 remain Draft/unmerged/untouched. UI/frontend development and integration remain paused.
- Next: (1) review latest exact-HEAD six-job CI, repair minimum semantics-preserving failure while working another nonconflicting non-UI lane; (2) Memory WAL/SHM, corrupt row and CAS/event prefix integrity; (3) Planner COMMIT-UNKNOWN quarantine plus exact registry-bound preaction audit; (4) Personal Context privacy veto, proactive synthetic recovery, Observation fixture provenance and V3 detached free-only guards.

**Overall ARK/JARVIS NOT_PASSED.**
