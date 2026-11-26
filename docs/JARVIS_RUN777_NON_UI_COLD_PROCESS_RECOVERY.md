# ARK Run777 — independent-process local recovery validation (NON-UI / FREE-ONLY)

**Scope:** optional synthetic/backend-only tests in Draft PR #8, with zero real
ToolBackend dispatch, no new account, secrets, paid APIs, GPU, protected model
evaluation, UI changes or main merge. **Overall ARK/JARVIS/V3: NOT_PASSED.**
All test claims concern disposable local SQLite and Python subprocesses,
not real hardware, authenticated approval, trusted clocks, external exactly-once
effects, independent custody, or cross-store atomicity.

## Exact starting point and work packages

- Work-basis `research/jarvis-foundations` HEAD:
  `914082034ec5bcf4ba9654742cf9e0ea50d78c8a`, Run776 status
  `docs/PROJECT_STATUS.md` blob
  `c26b0bc1e52807f840f89da256ea8301a4daa696`.
- **A — Atomic pre-action single-winner CAS:** commit
  `e099f4c4c6427c6d27412ceeae3ac84a99613fc8`, new
  `tests/test_atomic_independent_process_cas_run777.py`, two parametrized
  cases (same versus distinct occurrence identity). Two independent
  interpreter processes finish ledger bootstrap before being released
  concurrently with the same retained genesis. Assert exactly one durable
  intent+audit pair, the other claim fails, exact returned witness reopens,
  old genesis cannot inspect the newer ledger, and all authority flags remain
  False. A parent-held local WAL connection keeps sidecars stable during
  child initialization. This tests the local CAS transaction only.
- **B — Planner crash/terminal recovery:** commit
  `b3e10cb8c69f445a0f0ca73994c43d37bb03f177`, new
  `tests/test_planner_cross_interpreter_single_winner_run777.py`,
  two order-varied subprocess cases. Race a synthetic PENDING to RUNNING
  against PENDING to CANCELLED using one genesis prefix. Demand one committed
  transition only. After cold reopen, a winning RUNNING remains ambiguous,
  while winning CANCELLED propagates BLOCKED to a dependent step. No
  recovered state confers tool dispatch or replay. The stale genesis is not
  a valid second append.
- **C — Memory post-COMMIT UNKNOWN across restart:** commit
  `4631edbb3c1f85a2995d5c26d62968d705bb23b1`, new
  `tests/test_memory_cold_postcommit_review_run777.py`, two parametrized
  cases. A separate Python process commits the opt-in generation CAS and
  injects a READBACK failure strictly after the transaction, so it reports
  UNKNOWN. Fresh parent process reads one durable update and produces
  `ONE_MATCHING_UPDATE_OBSERVED`, or, after a separate newer update,
  `DIVERGED_OBSERVED`. Retained-generation replay must fail, and review
  attribution/retry/trusted-clock/consent/action flags remain False.
- **CI-grounded correction:** source/test HEAD
  `f07d0827776a00a19a326ce2c271018d5340d7ac`. Removed unused
  `Effect` import from Planner test (including the embedded child script).
  This addresses the actual `ruff F401` seen in CI; production code,
  enforcement, frozen evaluation and SQLite schemas were not weakened.

All three packages use only new opt-in tests, with **six parametrized cases**;
no production module/schema change. Subprocess race scheduling is nondeterministic
by design but outcomes must satisfy single-winner and safe-recovery invariants.

## Exact-head CI evidence / not-yet-validated statements

- Previous checkpoint HEAD `914082034...`: CI
  [#42908666795](https://github.com/Iam-2squared/ark-ai/actions/runs/42908666795)
  **six/six GREEN** (Ubuntu/Windows, Python 3.11–3.13). This is evidence for
  the old starting tree ONLY.
- Atomic test head `e099f4c...`: CI
  [#42918489020](https://github.com/Iam-2squared/ark-ai/actions/runs/42918489020):
  Ubuntu 3.13 GREEN, other jobs in progress at last early inspection.
- Planner test head `b3e10cb...`: CI
  [#42918659306](https://github.com/Iam-2squared/ark-ai/actions/runs/42918659306):
  **six/six FAIL at Ruff stage**, specifically unused
  `ark.agency.contracts.Effect` in the new Planner file; logs were read from
  Ubuntu and Windows jobs, and fixed at `f07d082...`.
- Memory test head `4631edb...`: CI
  [#42918899165](https://github.com/Iam-2squared/ark-ai/actions/runs/42918899165):
  also inherited the same Ruff F401 failure; no evidence of pytest failure
  or success at that head.
- Corrected three-package source/test head `f07d082...`: CI
  [#42919019548](https://github.com/Iam-2squared/ark-ai/actions/runs/42919019548)
  **IN PROGRESS at report creation**, with no exact-head six-job PASS
  claim. The subsequent report and checkpoint commits each require their
  own HEAD-specific CI evidence.

## Threat boundaries, independent gates, and next work

A durable SQLite transaction is not a globally exactly-once external action.
A recovered RUNNING entry is UNKNOWN and quarantined; no automatic retry.
Post-COMMIT diagnostic labels never prove which caller made the write. No
retained witness here has independent custody; separate Planner/Atomic/Memory
SQLite reads are not a coherent multi-store snapshot. Subprocess synchronization
is a synthetic test barrier, not a trusted scheduler, user consent or authentic
receipt. Failure of any six-job CI demands a log-grounded narrow correction
before marking a newer exact HEAD green.

PR #5 (V3 protected/paid learning gate) and paused UI PR #9 stay Draft and
untouched. V1/V2/Local UI/Launcher freezes and all human-review,
contamination/provenance, Candidate identity and evaluation boundaries remain.

**Next plan / 今後の方針:** (1) confirm all six corrected-head CI jobs; fix
any actual test failures without weakening original safety invariants;
(2) develop stronger transactional Memory COMMIT-UNKNOWN/expiry proofs and
Planner terminal recovery across restarts; (3) only after exact-head GREEN,
review isolated mock-only PermissionGate/ToolRegistry/audit-before-action
connections and privacy-safe Context/scheduler/observation guards; (4) keep
real tools, user data, physical PC, protected V2/V3 evaluation, training,
spending, credential connection, Candidate promotion and main merge blocked
without their explicit separate authorizations.


## Late CI-grounded Planner fix and independent privacy restart lane

- After this report was first saved, corrected test HEAD `f07d082...` CI
  [#42919019548](https://github.com/Iam-2squared/ark-ai/actions/runs/42919019548)
  reached pytest and failed two new Planner tests on Ubuntu 3.11, 3.12, 3.13;
  **12,739 other tests passed** in those Ubuntu environments. The losing
  interpreter raised `PlanConflictError: revision mismatch`, an intentional,
  fail-closed existing Planner CAS rejection, rather than the test fixture's
  too-narrow `SyntheticPlanJournalRejected` catch. **No production Planner
  code was changed.** The minimal test-only correction, commit
  `f40294dce4cb9358f21b83832e76a31a0739c514`, accepts either existing
  denial exception for the losing process and the stale-token second append;
  [CI #42919952417](https://github.com/Iam-2squared/ark-ai/actions/runs/42919952417)
  was in progress at last sampled status, with Ubuntu Python 3.11/3.13 GREEN.
- Independent fourth package **D — fail-closed local privacy veto restart**
  adds an opt-in `require_existing: bool = False` keyword to
  `DisconnectedPrivacyVetoLedger`, production commit
  `8ff8ee48ff990925a3dc919c6a5d14ab55656003`. A process explicitly
  recovering historical vetoes with `require_existing=True` will refuse
  to create a missing or uninitialized SQLite ledger. It uses SQLite
  `mode=rw` to prevent creation after the filesystem check. Normal
  default create/initialization is retained for new disposable fixtures;
  callers **must opt in** for existing-only restart safety. This does not
  authenticate user identity, persist a backup, survive a malicious path
  race, or prove global context erasure.
- Privacy regression file
  `tests/test_privacy_veto_require_existing_run777.py` at
  `9253de31a62bcca182f8eb4767e9226f458aa0c5` adds **seven
  parametrized cases** for missing/deleted source, existing veto continuity,
  uninitialized source refusal and exact-boolean restart mode. All deletion
  is confined to disposable `tmp_path`, not actual user data.
- Source-only privacy CI
  [#42920510439](https://github.com/Iam-2squared/ark-ai/actions/runs/42920510439)
  and combined source+test
  [#42920585697](https://github.com/Iam-2squared/ark-ai/actions/runs/42920585697)
  were in progress/queued at last inspection. **Latest 6/6 GREEN for these
  newer HEADs is not yet established.**
- Total invocation after these corrections: **four meaningful work packages**
  (three new test packages and one production privacy package with new
  regression tests), **thirteen parametrized new cases**, and two real-log
  test corrections (F401 and losing-process exception type). No new
  paid compute, real WRITE, frontend change, protected evaluation or merge.

**Next:** confirm new exact-head six-job CI (especially the independent
privacy restart tests), amend only reproducible failures, and preserve the
single-winner, no-auto-replay and privacy-veto invariants.
