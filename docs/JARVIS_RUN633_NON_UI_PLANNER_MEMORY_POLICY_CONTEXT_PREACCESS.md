# ARK AI Run633 — Non-UI callback-boundary and private-carrier custody

**Scope:** Draft PR #8 `research/jarvis-foundations` only; no UI, actual
ToolBackend call, model weights, Candidate, external compute, paid API, account
connection, disclosure, irreversible erasure, protected evaluation or merge.
All checks are local fail-closed diagnostics, **not authenticated consent,
trusted time, physical custody or real-world exactly-once execution**.

## Exact work basis and four independent implementation packages

- **Invocation starting PR #8 HEAD:** `00a916ea1b930cf2980bf18edd21085600b21c96`.
  Prior exact-head [CI #42018979783](https://github.com/Iam-2squared/ark-ai/actions/runs/42018979783):
  completed **6/6 GREEN**, Ubuntu and Windows Python 3.11–3.13, confirmed by
  the job list at invocation start. Frozen main and PR #5/#9 were not written.
- **Planner post-snapshot carrier preaccess:** source
  `0f928740731b8bf30e771238deef3c7a495d1c45`,
  `src/ark/agency/planner_journal_review.py`. The untrusted/reentrant
  `_snapshot(graph, tail)` can rebind a `SyntheticPlanRecovery` slot or
  `__getattribute__` *after* an earlier constructor check. The returned
  result's original fields, lookup hooks and denial properties are now
  checked **before the first field read**. Test
  `tests/test_planner_snapshot_postcallback_preaccess_run633.py` was created
  at `23bc59b1548da96514e660815aa34529405be215`: **12 new parameter
  cases**, including `recover` and pre-COMMIT `append`.
- **Memory coherent multi-namespace snapshots:** source
  `ab72d123bfc6ed43750af8676056766268e8fc4d`,
  `src/ark/memory/coherent_snapshot_review.py`. Import-original request and
  result class field descriptors and `__new__`/`__getattribute__`/`__getattr__`
  are checked statically. The request's epoch check now precedes every
  caller-owned request property read, including after clock and hashing
  callbacks. Test `tests/test_memory_coherent_request_result_slots_run633.py`
  created at `f304c353ce75f1329b7ad6c1e71ad6e44a3b8b81`: **16 cases**.
  No personal-context connector or database schema change.
- **CapabilityGrant admission/one-shot token preaccess:** source
  `bb028eb06dbb29e005ce092ba58f93b201eb74ed`,
  `src/ark/agency/policy.py`. Original `CapabilityGrant` field slots and
  lookup hooks must match before direct and registry-bound policy field
  reads, throughout grant enumeration and under the WRITE token lock. Test
  `tests/test_permission_grant_slot_preaccess_run633.py`
  `9d7f5cfb5bb5602ffbaf4166ed9df35a576aaa4e`: **28 cases**,
  including generator-end mutation and unchanged local READ/WRITE behavior.
  This does not create durable approval or dispatch tools.
- **Personal Context private synthetic fixtures:** source
  `a2864c6b7d37b0313215769ee00d560a369133f2`,
  `src/ark/personal_context_offline_preview.py`. Static import-original
  `OfflineContextFixture` and `OfflineContextPreview` input/output slots,
  constructors, lookup hooks and existing denial flags are checked before
  private fixture reads, including after reentrant digest callbacks. Test
  `tests/test_personal_context_fixture_slot_guard_run633.py`
  `f4e42aa3bfac6fdd4dd826ce7ec2d7ba270f9aaf`: **16 cases**.
  Privacy flags remain all False; fixtures are not real user profiles.

**Authored new parameterized cases: 72 total (12 + 16 + 28 + 16).**
These are committed *test cases*, not local pytest PASS counts. No local
pytest/Ruff result was obtained; only exact GitHub CI jobs can establish
platform success.

## CI-driven corrections without weakening guards

- Planner [CI #42021512465](https://github.com/Iam-2squared/ark-ai/actions/runs/42021512465)
  Ubuntu Python 3.11 recorded **2 FAIL / 8,948 PASS / 1 SKIP**.
  The two failures were test-fixture `monkeypatch.setattr` defaulting to
  `raising=True` for absent `__getattr__`. Test-only correction
  `a48250e690b6ce6d5a6842892c610e0712181399` uses
  `raising=False`. Production preaccess refusal is unchanged.
- PermissionGrant [CI #42022146490](https://github.com/Iam-2squared/ark-ai/actions/runs/42022146490)
  Ubuntu Python 3.12 recorded **4 FAIL / 8,990 PASS / 1 SKIP**:
  two expected Planner fixture failures plus **two genuine direct-policy
  failures**. The generator's StopIteration/finally changed `grant.scope`
  before the policy's final post-iterator read, causing a forged property to
  execute. Source correction
  `659f48eb942fc55fead33fac2083f4ed58a9b371` calls the existing
  `assert_iteration_epoch()` immediately after grant iteration and before
  any retained field read or token spend. Not a grant/expiry relaxation.
- Personal Context [CI #42022328877](https://github.com/Iam-2squared/ark-ai/actions/runs/42022328877)
  Ubuntu Python 3.13 recorded **7 FAIL / 8,987 PASS / 1 SKIP**,
  including the above four and three old test expectations that demanded
  later denial after a forged `__getattribute__` had run. Corrected
  `tests/test_personal_context_preview_final_epoch_run498.py` in
  `612cbc47fabcbb3c693d99cf0704176f2911380b`
  to require the original descriptor refusal *before execution*.
  Existing tests still check false-only non-authority.
- **At report preparation**, repaired source/test HEAD
  `659f48eb942fc55fead33fac2083f4ed58a9b371`,
  [CI #42023042238](https://github.com/Iam-2squared/ark-ai/actions/runs/42023042238)
  **QUEUED**; latest six-platform GREEN is **NOT** confirmed. This
  report and the eventual checkpoint trigger their own PR CI.
  No manual workflow reruns or duplicate workflow dispatch were launched.

## Frozen boundaries, blockers and next engineering work

PR #5 remains Draft/unmerged at `805b377697472268db02650a89c7a94b1c5337c8`,
PR #9 remains Draft/unmerged at
`3b49048dd70eebcb6268299b9ecef4e301bbc0fd`,
main/base remains `7a843f17eb96ed13d66f23b58b06406b3002e405`.
All new UI/frontend development is PAUSED. V1/V2/Local UI/Launcher evidence
and frozen V3 Contract 1 are untouched. No paid or potentially billable
actions, external GPU/API, credentials, physical-PC tasks, human consent or
review, real Candidate/adapter, V2 final evaluation, Candidate promotion,
actual ToolBackend/camera/mic, real notification, automatic UNKNOWN replay,
destructive deletion or approval-requiring main merge occurred.

Next: verify exact-head CI Ubuntu/Windows × Python 3.11–3.13 and repair
actual logged regressions; then advance Memory CAS/event/high-water coherence,
Planner durable restart transitions, registry-bound token/Audit/Occurrence
non-executing integration, privacy lifecycle, and free-only V3 passive guards.
No synthetic SHA/clock/SQLite receipt is authenticated authority.

**ARK / JARVIS / V3: NOT_PASSED.**
