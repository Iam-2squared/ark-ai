# ARK AI Run687 — Cross-Store Mock Independence, Memory Privacy CAS, Scheduler Restart

## Scope / evidence classification

Free-only, disconnected, non-UI, non-executing regression packages on Draft PR #8, based initially on checkpoint HEAD `0543f25278b26009183841fb7f76df6fe14d8232` (Run686). This is test/evidence development, **not** external execution, authenticated consent, certified data erasure, or a JARVIS/V3 PASS. Main, Draft PR #5/#9 and frozen V1/V2/Local UI/Launcher contracts remain untouched.

The incoming Run686 exact HEAD CI [#42375217641](https://github.com/Iam-2squared/ark-ai/actions/runs/42375217641) was independently checked on 2026-11-07 JST: **6/6 GREEN**, Windows and Ubuntu × Python 3.11–3.13. This exact-head attestation permits independent mock-only integration without claiming production authority.

## Package A — independent mock plans, shared durable stores

`tests/test_synthetic_independent_plan_unknown_run687.py`: **5 parameterized scenarios** for stops after RUNNING, occurrence reservation, pre-action audit, audit-link COMMIT and local mock marker. The UNKNOWN plan is left RUNNING with no automatic replay. A separate plan, distinct request/one-shot token/occurrence, uses the **same** occurrence, audit and link SQLite files and immutable registry, without activating a real backend. The later success cannot release the prior plan's ambiguity or authorize a replay. Committed at `9e8739eee83955a6c4a3ec03c5dc3f2fc8c17a48`; import grouping corrected at `42620dc018204b60ee8d96200aef481e0d63f592`.

## Package B — generation CAS and privacy revocation across handles

`tests/test_private_revocation_memory_cas_integration_run687.py`: **3 parameterized scopes** (other owner, other namespace, both). First a local generation-fenced CAS commits; a separate SQLite revocation veto is recorded; a disjoint Memory CAS advances the global Memory event history; independently reopened readers must still see the same scoped revocation without content disclosure. The unrelated scope's `revoked` flag stays false, but its diagnostic still grants **no** context authority. The original fixture accidentally used a writer clock lower than the persisted Memory time floor, correctly causing three `MemoryConflictError: generation CAS clock regressed` failures. Only the test writer clock was advanced monotonically in `07e4307a566dd3d49fca7c7ba2be297a4f48c67e`; no production clock/CAS/privacy gate was weakened.

## Package C — expired-slot scheduler restart without notification

`tests/test_schedule_quarantine_restart_next_slot_run687.py`: **9 scenarios** spanning one-slot/two-slot retained quarantine prefixes, the next slot's NOT_DUE/DUE_UNVERIFIED/EXPIRED_QUARANTINE classification, full exhaustion, stale restart witness and clock rollback. It integrates `DisconnectedScheduleQuarantineLedger`, `DisconnectedScheduleCursor` and `review_offline_schedule_resume` with synthetic caller time. Every result is denial-only; the ledger is only inspected after restart and never sends notifications or executes tools. Committed at `53966de23f79d3ad72fef4abc76f5468fdc3d5e2`.

## CI / validation and corrections

- [#42378740214](https://github.com/Iam-2squared/ark-ai/actions/runs/42378740214), package A initial HEAD: **FAIL 6/6** on Ruff import-group formatting, test-only. No source test ran to completion on those jobs.
- [#42378848953](https://github.com/Iam-2squared/ark-ai/actions/runs/42378848953), package B ancestor: inherited the same Ruff issue; **FAIL 6/6**.
- [#42378934789](https://github.com/Iam-2squared/ark-ai/actions/runs/42378934789), package C ancestor: likewise inherited Ruff issue; **FAIL**.
- [#42378982621](https://github.com/Iam-2squared/ark-ai/actions/runs/42378982621), first Ruff-corrected source/test head: Ubuntu Python 3.11 reported **10,420 PASS, 1 SKIP, 3 FAIL**, all from the test's intentionally strict Memory clock floor; no Planner/Scheduler mock failure surfaced in that completed job. Corrected fixture HEAD `07e4307a566dd3d49fca7c7ba2be297a4f48c67e` is newer and must independently pass; ancestor GREEN is not applicable.
- Latest corrected HEAD CI **IN PROGRESS / NOT YET ATTESTED** when this report was authored. The checkpoint commit will create its own distinct CI. No duplicate equivalent manual workflow run was launched.

## Boundaries / outstanding truth gaps

This code uses local independent SQLite stores and caller-supplied synthetic time; no cross-store atomic transaction, authenticated historical writer, trusted approval issuer, true external exactly-once execution, global erasure, consent, media capture, live computer action, or training permission is established. Retained hashes detect local drift; they are not independent provenance. Unknown WRITE outcomes must stay **NO AUTOMATIC REPLAY**. Draft PR #5 still requires immutable model/tool/file identities, reviewed 120/30 provenance/rights/contamination, a proposed specific GPU/budget/time packet and separate explicit approvals **before any paid external compute**; protected V2 final evaluation, Candidate and promotion remain blocked.

## Next work

1. Verify exact-head CI after the Memory test clock correction, inspect failed job logs if necessary and apply only normal Contents API changes.
2. Stress test independent occurrence+audit+link crash interleavings and Planner step receipt recovery without dispatch, after this lower-layer exact-head GREEN.
3. Continue coherent Memory CAS/ABA/WAL/expiry and privacy snapshot boundaries; maintain consent/erasure denials.
4. Continue disconnected scheduler and observation fixture contracts, preserving complete UI pause and all frozen/pass gates.
