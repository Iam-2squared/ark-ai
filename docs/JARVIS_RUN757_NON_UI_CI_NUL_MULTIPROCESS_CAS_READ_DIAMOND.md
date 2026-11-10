# Run757 — CI repair, independent Memory processes, detached READ diamond

**Scope:** FREE-ONLY / NON-UI / disconnected synthetic foundations. Work basis:
[Run756 checkpoint](https://github.com/Iam-2squared/ark-ai/commit/82206edfde65f267cc235cd86317572801c67b8c)
on Draft PR #8. Source and frozen contracts are not changed by the test-only
packages below. This report is an evidence log, not a PASS or authorization.

## 1 — Actual Run756 CI failure and safe test correction

The exact checkpoint HEAD `82206edfde65f267cc235cd86317572801c67b8c`
failed all six Python/OS jobs in
[CI #42758885897](https://github.com/Iam-2squared/ark-ai/actions/runs/42758885897).
The Ubuntu Python 3.11 log reports **6 FAILED / 12,409 PASSED / 1 SKIPPED**;
Windows Python 3.11 reports **6 FAILED / 12,336 PASSED / 74 SKIPPED**.
All six failures are older parameterizations in
`tests/test_observation_fixture_nul_framing_run745.py`. The Run756 adapter
now correctly rejects embedded NUL in `source_id`/`privacy_scope` before
hashing caller-private bytes. The older test assumed the *adapter* accepted
NUL and only the later optional chain reviewer would reject it.

[test-only correction `1f46e400`](https://github.com/Iam-2squared/ark-ai/commit/1f46e400d5e02441d3cbdd5370bc6a751686dd20):
each of the same six NUL cases now verifies early adapter rejection, and
constructs an inert, frozen `ObservationEnvelope` directly to independently
retain the chain reviewer's own NUL-framing rejection. No adapter/source safety
check was removed; no sensor, real content or backend is touched.

## 2 — Independent-process generation-fenced SQLite CAS

[test-only `066c2684`](https://github.com/Iam-2squared/ark-ai/commit/066c2684ac282e47b0b9bb451ee0d0e1e410c4c2) adds
`tests/test_memory_generation_multiprocess_recovery_run757.py` with three
authored pytest cases:

- Two separately spawned Python processes compete for one retained generation
  CAS token on the same disposable SQLite Memory v1 file. After release of an
  explicit synchronization gate, exactly one update may commit, with one
  stale-token conflict, a single update event, and no replay on restart.
  Two input variants are parameterized.
- A spawned process commits but provides **no application-level result
  receipt** to the parent. The parent performs a fresh SQLite read and
  generation observation instead of blindly retrying. The original token
  must conflict; event sequence must remain create→update.

These are true OS-process regression fixtures, not external exactly-once
proofs. No real user files, production retention, trusted time, actor identity,
irreversible effects or external action authorization are involved.
Cross-process path/WAL metadata and OS scheduling are still not cryptographic
provenance.

## 3 — Detached READ recovery: dependency diamond

[test-only `eabdb048`](https://github.com/Iam-2squared/ark-ai/commit/eabdb04886106528d62a3220f9649f749de7fba2) adds
`tests/test_detached_read_recovery_diamond_run757.py`, **24 authored cases**:
five root-state/fan-in propagation outcomes, sixteen contradictory started-child
histories, and three multi-hop terminal/unknown propagation cases. A disjoint
READ stays mock-ready when unrelated branches are blocked, but no recovery
schedule grants `dispatch_authorized`, `automatic_replay_authorized` or
`external_outcome_verified`. No real tool dispatch is possible here.

## Verified vs not verified

The first three GitHub Contents API commits were successfully written; these
are **27 new authored pytest cases (3 Memory + 24 Planner), plus six old
Observation cases rewritten to preserve both refusal boundaries**.
Static source inspection found no changed-line >100 character violations in
the three touched test files. That does **NOT** constitute a pytest, Ruff or
Windows PASS.

CI observed while preparing this report:
- [#42764073025](https://github.com/Iam-2squared/ark-ai/actions/runs/42764073025) — `eabdb04886106528d62a3220f9649f749de7fba2`: IN_PROGRESS
- [#42763942617](https://github.com/Iam-2squared/ark-ai/actions/runs/42763942617) — `066c2684ac282e47b0b9bb451ee0d0e1e410c4c2`: IN_PROGRESS
- [#42763728217](https://github.com/Iam-2squared/ark-ai/actions/runs/42763728217) — `1f46e400d5e02441d3cbdd5370bc6a751686dd20`: IN_PROGRESS
- [#42758885897](https://github.com/Iam-2squared/ark-ai/actions/runs/42758885897) — `82206edfde65f267cc235cd86317572801c67b8c`: COMPLETED/FAILURE

**No new HEAD may be declared GREEN merely because a previous HEAD passed.**
Do not re-run equivalent workflows manually. Diagnose new failures from actual
job logs and perform the smallest safe correction; keep workstreams separate
while CI is in flight.

## Immutable boundaries and next gates

- V1/V2, Local UI, Launcher, frozen evaluation/contracts and main unchanged.
- V3 Draft PR #5 remains gated/unmerged; passive snapshot gate still shows
  unapproved base/tokenizer hashes, human-reviewed 120/30 rights/contamination,
  runtime/device identities and a user-approved hard JPY/time ceiling. No
  real training, Candidate, protected V2 opening or external GPU.
- UI Draft PR #9 remains paused and untouched; no frontend work.
- No paid service, new credential, production action, human approval invention,
  promotion or main merge. Review-only receipts remain deny-only.

**Next plan / 今後の方針:** (1) validate latest exact-head six-platform CI;
(2) repair any new failure without weakening refusal contracts;
(3) after GREEN, develop independently witnessed Memory COMMIT-UNKNOWN/readback,
Planner durable recovery, audited mock-only registered authorization;
(4) keep V3 free-only evidence boundaries and privacy/legal consent blockers
explicit. ARK/JARVIS/V3 remains **NOT_PASSED**.
