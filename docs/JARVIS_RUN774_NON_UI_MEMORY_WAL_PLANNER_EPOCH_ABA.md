# ARK AI — Run774 non-UI Memory WAL / Planner epoch / ABA evidence

**2026-11-11 JST.** All work on open Draft PR #8, branch `research/jarvis-foundations`. Source/test work-basis: Run773 checkpoint HEAD `7d34238b7cbaa249e9e77c06d575bac9655ccd12`. Latest source/test HEAD in this report: `9861fee4de935d965d9fb4c46101f5e3887d0d20`. This report is an inert technical record, not a certification, independent attestation or permission to operate.

## Three independent packages

1. **Run425 Memory cross-process expiry/delete CAS harness repair** — commit `ac0513e20694aa1ded40e4b6fae1656175bbffee`, file `tests/test_memory_cross_process_expiry_delete_race_run425.py`. Preserve the actual concurrent delete/expiry-versus-refresh CAS gate. Initialize subprocess SQLite stores sequentially and hold a WAL keeper connection throughout, avoiding SQLite WAL sidecar unlink/bootstrap races that do not measure CAS correctness. Capture child stdout/stderr on early exits; retain the original single-effect/event/row assertions. **No Memory production source, schema or custody policy changed.** This targets a previously observed CI failure; it does not prove absence of other independent race failures.

2. **Planner retained recovery epoch recheck** — source commit `5dc1262710785c45473048b74e235ea662409839`, `src/ark/agency/disconnected_planner_epoch_recheck.py`; tests commit `6ab9167d860434521743ce0546146308a0892342`, `tests/test_planner_detached_epoch_recheck_run774.py`. New exact-type, deny-only fixture compares a previously detached Planner recovery with a fresh local journal replay requiring an earlier retained prefix. Five tests cover current-at-read, later terminal event drift, forged historical prefix, corrupted SQLite header and replay method substitution. `MATCH_AT_READ` **is neither a lease nor a cross-store snapshot**, and a commit can happen immediately after comparison. No actual ToolBackend is available through this fixture.

3. **Memory cold-process lifetime ABA** — commit `9861fee4de935d965d9fb4c46101f5e3887d0d20`, `tests/test_memory_cold_process_generation_aba_run774.py`. Two parameterized cases execute a fresh Python interpreter that expires or explicitly deletes an owner-scoped Memory record and recreates the same deterministic identity at revision 1. The parent process verifies create-event generation advanced, refuses the old CAS token, retains its new row, keeps a separate owner's generation valid and checks the global event IDs. Local synthetic clocks only; no wall-clock trust or external effect assumed.

## Exact-head CI and limitations

- **Previous Run773 checkpoint:** [Actions #42884501127](https://github.com/Iam-2squared/ark-ai/actions/runs/42884501127) — **6/6 GREEN** (Ubuntu/Windows × Python 3.11–3.13), applies only to `7d34238b...`.
- **Run774 package A HEAD `ac0513e...`:** [Actions #42887936359](https://github.com/Iam-2squared/ark-ai/actions/runs/42887936359) — Ubuntu **3/3 GREEN**, Windows **IN PROGRESS** at last sampled jobs.
- **Run774 package B source HEAD `5dc1262...`:** [Actions #42888289267](https://github.com/Iam-2squared/ark-ai/actions/runs/42888289267) — Ubuntu **3/3 GREEN**, Windows **IN PROGRESS**.
- **Run774 package B test HEAD `6ab9167...`:** [Actions #42888483540](https://github.com/Iam-2squared/ark-ai/actions/runs/42888483540) — Ubuntu **3/3 GREEN**, Windows **IN PROGRESS**.
- **Run774 package C HEAD `9861fee...`:** [Actions #42888796578](https://github.com/Iam-2squared/ark-ai/actions/runs/42888796578) — **IN PROGRESS** at last sampled jobs, no full six-job conclusion.
- **No local full-suite pytest claim.** Each GitHub Contents write can launch a new workflow. The administrative report/checkpoint HEADs are newer and must have their own CI independently verified. These results do **not** justify a Run774/latest-head 6/6 PASS claim.

## Frozen boundaries and next gates

Draft PR #5 is protected/unmerged; paused UI Draft PR #9 is untouched/unmerged; main, V1/V2/Local UI/Launcher, ObservationEnvelope v1, frozen evaluation/evidence/contamination/rights contracts remain unchanged. No UI development. No external or potentially billable compute, model training/Candidate promotion, secrets, new accounts, real tool execution, protected evaluation, real notification/sensor access, physical PC actions, irreversible actions or main merge.

Local SQLite append consistency and per-row CAS do not provide authenticated writer provenance, externally retained historical custody, a trusted clock, consent, a simultaneous Planner–Atomic transaction, or external exactly-once side effects. Recovered RUNNING/WRITE remains **UNKNOWN/MANUAL-ONLY**.

**Next plan / 今後の方針:** (1) inspect exact Run774 CI failures and fix only confirmed causes using normal GitHub Contents writes; (2) preserve deterministic process bootstrap without relaxing storage preflights; (3) once source/test HEAD is GREEN, explore **optional** detached Planner epoch check before manual atomic triage, with explicit after-read race limitation; (4) continue Memory expiry/ABA/COMMIT-UNKNOWN and Personal Context privacy isolation; (5) maintain frozen V3 free-only approval/path/identity safeguards until explicit gates.
