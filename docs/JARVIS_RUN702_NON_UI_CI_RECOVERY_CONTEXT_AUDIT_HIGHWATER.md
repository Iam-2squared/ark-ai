# ARK AI — Run702 non-UI core / 2026-11-08 JST

> **DRAFT / NOT_PASSED.** All work is FREE-ONLY, local/disconnected/mock-only,
> and reversible. No UI/frontend changes, paid or external GPU/API action,
> actual Candidate training, protected V2 opening, real tool dispatch, user
> account connection, physical-PC action, frozen-contract edit or main merge.

## Starting evidence and scope

- Repository `Iam-2squared/ark-ai`; initial work-basis PR #8 HEAD
  `a235e56b4f964dac08d15cff817d28c0ab9d767f`.
- PR #8 remains Draft/unmerged; PR #5 is separately gated Draft, PR #9 is
  Draft/unmerged with all new UI/frontend development PAUSED.
- Ordinary GitHub Contents API writes only, each after a fresh exact branch HEAD
  check and (for existing files) fresh blob-SHA read. No force push, raw Git
  object fabrication, safeguarded-path bypass, or destructive operation.
- Four meaningful packages: (A) CI Ruff repair; (B) Personal Context restart
  ledger access-hook custody and 5 new tests; (C) read-only Action Audit suffix
  high-water review and 5 new tests; (D) 8 legacy Planner early-refusal
  expectations corrected across three files. **10 new authored regressions**
  plus 8 legacy tests aligned. These are NOT a claim of suite PASS.

## A — Actual exact-head lint blocker resolved

- Previous final [Run701 CI #42440545374](https://github.com/Iam-2squared/ark-ai/actions/runs/42440545374)
  failed all six Linux/Windows jobs at `ruff check .`: the newly widened
  expected Memory event-high-water diagnostic made line 71 of
  `tests/test_memory_event_causality_run479.py` 101 characters.
- [Commit `ab5b90aa`](https://github.com/Iam-2squared/ark-ai/commit/ab5b90aab8472e252de344b98cd8844897b640f7)
  only parenthesizes that assertion over multiple lines. The intended
  event-corruption refusal and Memory production source remain unchanged.
  The corrected-head [CI #42444123278](https://github.com/Iam-2squared/ark-ai/actions/runs/42444123278)
  passed Ruff but exposed the eight separate Planner legacy-test failures below.

## B — Personal Context restart, exact ledger lookup-hook custody

- [Source `3dabb4b6`](https://github.com/Iam-2squared/ark-ai/commit/3dabb4b6dc839bde6ae09f7808c36b20bbc9ef3c)
  import-pins the original `DisconnectedContextReplayLedger` class and its
  `__getattribute__`/`__getattr__` hooks. The read-only restart review
  rejects altered class lookup hooks **before first ledger path access**,
  and at each repeated retained/observed source-epoch check.
- [Tests `6985a768`](https://github.com/Iam-2squared/ark-ai/commit/6985a7683be1d7b9a276f3cddd12d99b1332e639):
  **5** cases: two preinstalled hostile hooks, two hooks installed by the
  in-flight witness callback, and an intact no-disclosure baseline.
  Hook-mutation fixtures run in isolated local Python subprocesses to avoid
  CPython class-slot poisoning of unrelated tests. They require **zero hostile
  callback invocations**, not merely an eventual exception.
- This protects local read-only diagnosis only. No authentic user consent,
  trusted source, external historic prefix, account access, disclosure
  authority, or automatic replay is established.

## C — Audit continuity, suffix and AUTOINCREMENT high-water

- [Source `787e61f2`](https://github.com/Iam-2squared/ark-ai/commit/787e61f258605951dacfa007f47ef936c73911ff)
  reads the existing `sqlite_sequence` high-water for `action_events`
  inside the **same read-only SQLite transaction** as its audit rows.
  The final check catches deleted terminal events, fully emptied formerly
  populated ledgers, and missing/forged sequence rows even when surviving
  event IDs are individually gap-free.
- Preserves earlier diagnostic precedence: explicit missing first/middle
  events are still detected by existing ID-gap logic, and a retained witness
  is still checked for `shorter history` before the additional high-water
  fence. Frozen v1 audit DDL, outcome semantics and write APIs are unchanged.
- [Tests `cb5b3310`](https://github.com/Iam-2squared/ark-ai/commit/cb5b33105fb2833ee5c24e55fa4d96a197d95463):
  **5** cases: deleted last event; deleted all events; artificially lowered
  `sqlite_sequence`; deleted sequence row; successful unrelated append
  across local SQLite restart. All use disposable synthetic local records.
- A writer with permission to rewrite both rows and `sqlite_sequence`
  can fabricate a consistent local state. This does **not** establish
  externally custodied audit, hardware-backed time or exactly-once effects.

## D — Actual Planner test failure diagnosis and semantics-preserving fixes

- Corrected-head Ubuntu Python 3.11 [CI #42444123278](https://github.com/Iam-2squared/ark-ai/actions/runs/42444123278)
  actually reported **10,839 PASS, 1 SKIP, 8 FAIL**.
  The new Run701 Planner class lookup descriptor pinning rejects substituted
  `__getattribute__` **before** hostile callbacks execute; three old test
  files still expected later carrier-change diagnostics and/or the malicious
  callback to execute.
- Test-only [commits `df7ca952`](https://github.com/Iam-2squared/ark-ai/commit/df7ca952049c57aa3e49f2701a2dc4075f5d51bf),
  [`c5b4e1af`](https://github.com/Iam-2squared/ark-ai/commit/c5b4e1af2d1b7f07cc5da884d1d9e04dfa0a8f2e),
  and [`3dcb54ba`](https://github.com/Iam-2squared/ark-ai/commit/3dcb54bae2ee9fd4a5e73ef4e67d0a31a40572a4)
  update exactly **8** legacy expectations in
  `test_read_recovery_decision_custody_run475.py`,
  `test_read_recovery_denial_descriptor_epoch_run546.py`, and
  `test_read_recovery_late_denial_run516.py`.
  The corrections explicitly require the early authority-descriptor denial,
  **zero invoked malicious callbacks**, and intact input carriers.
  **No Planner production check was weakened.**
- These corrections still require a new six-environment CI run to verify
  all cases. A previous failure is not retroactively a PASS.

## Evidence limits and prioritized next plan

- Each CI run is tied to its own exact source/test HEAD. Early runs including
  [#42444266869](https://github.com/Iam-2squared/ark-ai/actions/runs/42444266869)
  (Context tests), [#42444370723](https://github.com/Iam-2squared/ark-ai/actions/runs/42444370723)
  (Audit tests), and [#42444499770](https://github.com/Iam-2squared/ark-ai/actions/runs/42444499770)
  (Planner corrections) were IN PROGRESS or QUEUED at first review; none is
  represented as final 6/6 GREEN. The report and checkpoint will create
  additional CI heads requiring independent checks.
- The static 100-character line screening of new/modified sources and tests
  showed no over-length lines. That screening is **not pytest or Ruff PASS**.
- Next: (1) get exact final-head six-job verdict, fix only real failures and
  overlap safely on other non-UI modules; (2) Memory CAS/ABA, COMMIT-UNKNOWN,
  retained privacy/WAL integrity; (3) Planner per-step durable READ and UNKNOWN
  proofs; (4) registry-bound exact-type PermissionGate, restart-safe audit-before-
  action with mock/disconnected execution; (5) Privacy/Proactive/Observation
  local-first backends and free-only V3 review.
- Keep PR #5/#8/#9 Draft/unmerged, all frozen V1/V2/Local UI/Launcher
  contracts/evidence intact, protected V2 evaluation unopened, UI paused,
  and Candidate/paid GPU/user approvals **blocked**.

**ARK/JARVIS/V3 completion state: NOT_PASSED.**
