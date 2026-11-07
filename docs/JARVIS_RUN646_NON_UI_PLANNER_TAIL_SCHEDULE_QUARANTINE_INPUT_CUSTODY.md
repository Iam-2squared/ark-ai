# ARK AI — Run646 non-UI journal-tail and schedule-quarantine carrier custody

**Scope:** isolated reversible JARVIS core foundations in Draft PR #8; no UI, real tool
execution, scheduler activation, external compute, new credentials, V2 protected
evaluation, or contract changes. ARK/JARVIS remains **NOT_PASSED**.

**Work-basis HEAD:** `0f052081701f036af57131f9c8dade954b36d401`
(Run645 checkpoint, [six-job CI GREEN](https://github.com/Iam-2squared/ark-ai/actions/runs/42132706849)).

## Package A — Planner retained-tail descriptor custody

- Source `src/ark/agency/planner_journal_review.py`, commit
  `32b9a4d8dbf11d6a7f4870603b61052e6e912290`.
  Bind the import-time `SyntheticPlanTail` class, its five slotted fields,
  constructor and attribute lookup hooks. The existing recovery-DTO
  integrity guard now rejects a replaced tail class/descriptor before the
  initial `recover` or `append` retained-witness field access.
- Independent test `tests/test_planner_tail_preaccess_custody_run646.py`,
  commit `5e69f90977245abd4d47914b39ab911e1c619aa5`.
  **17 authored cases**: five slot descriptors × read/write, three lookup
  hooks × read/write, and one clean restart with persistent RUNNING/UNKNOWN.
  Preinstalled poisoned descriptors must not execute or open SQLite.
- The existing synthetic `assert_shape` callback-injection contract and
  failure diagnostics are not changed. This is **preinstalled carrier
  hardening**, not a claim of comprehensive protection against all
  reentrant callbacks or post-COMMIT source mutations.

## Package B — disconnected proactive schedule input custody

- Source `src/ark/disconnected_schedule_quarantine_ledger.py`, commit
  `de4cc438f349232d8c77941c43abc2b305f439c7`.
  Bind exact `QuarantinePolicy` and `QuarantineWitness` input classes,
  slotted fields and constructor/attribute hooks at import. Before
  `_policy_epoch` and the retained `_check_witness` access inputs,
  reject class-level executable substitutions without reading fields
  or opening the SQLite ledger.
- Independent test `tests/test_schedule_quarantine_input_slots_run646.py`,
  commit `687d9f35b13b1dba3a433f9daaa6d8ba5612fefc`.
  **27 authored cases**: seven input slot substitutions × inspect/write,
  three hooks × two input classes × inspect/write, and one valid synthetic
  quarantine flow with all deny-only flags False.
- Existing receipt denial-getter detection remains at its established
  post-COMMIT boundary; a stored quarantine row is never rolled back merely
  because a returned receipt was rejected. The policy, local clock and
  witness remain caller-controlled and unauthenticated.

## CI and evidence classification

- Run645 checkpoint HEAD `0f052081701f036af57131f9c8dade954b36d401`:
  [CI #42132706849](https://github.com/Iam-2squared/ark-ai/actions/runs/42132706849),
  **GREEN (Ubuntu/Windows × Python 3.11, 3.12, 3.13, 6/6)**.
- Planner source:
  [CI #42139268053](https://github.com/Iam-2squared/ark-ai/actions/runs/42139268053),
  **in progress at last inspect** (Ubuntu 3/3 GREEN).
- Planner source plus tests:
  [CI #42139350258](https://github.com/Iam-2squared/ark-ai/actions/runs/42139350258),
  **in progress at last inspect**.
- Quarantine source:
  [CI #42139537960](https://github.com/Iam-2squared/ark-ai/actions/runs/42139537960),
  **in progress at last inspect**.
- Quarantine source plus tests:
  [CI #42139613293](https://github.com/Iam-2squared/ark-ai/actions/runs/42139613293),
  **in progress at last inspect**.
- Total **44 regression cases authored**, **not** a pytest PASS count.
  No local pytest/Ruff or physical-PC execution claimed. All new
  validation still requires exact-head CI verification. Do not interpret
  older CI successes or queued jobs as latest-head GREEN.

## Security, isolation and limitations

Local SQLite uniqueness and replay-only witnesses do not authenticate writers,
user consent, a trusted wall clock, memory content provenance, external effects,
or independent evidence custody. A recovered RUNNING plan step is UNKNOWN and
non-replayable, and quarantined overdue occurrences cannot notify or dispatch.
These changes are additive, do not alter frozen V1/V2/Local UI/Launcher
contracts, and leave Draft PR #5/#9 and main unchanged.

**Next:** establish latest exact-head six-job CI; repair any real failures
through ordinary Contents updates only. Continue Memory COMMIT-UNKNOWN and
event/row continuity, Planner replay boundaries, and separate mock-only
ToolRegistry/PermissionGate/audit-before-action integration; keep UI paused.
