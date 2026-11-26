# Run644 — Mock-link restart fix, Memory event-prefix custody, Planner terminal race

## Scope and authority

All changes are on **Draft PR #8** (`research/jarvis-foundations`). Source,
test, and evidence changes are disconnected/local-only: no external effect,
backend dispatch, human authorization, paid service, model training or UI work.
The ARK/JARVIS and V3 completion gates remain **NOT_PASSED**.

- Initial invocation work-basis HEAD: `7e05e35a353f960beea334b688278d0b949220cf`.
- Inherited [CI #42117507469](https://github.com/Iam-2squared/ark-ai/actions/runs/42117507469):
  **FAIL, all six jobs**, not GREEN. Ubuntu 3.11 reported
  **9,191 PASS / 1 FAIL / 1 SKIP**. The failing assertion expected zero
  audit links at fault `after_mock_marker`, but the reviewed mock cycle
  persists its audit-link record **before** calculating the local marker;
  the durable link witness correctly had `event_count=1`.
- Fix `3cf06f2e5f068e17fc6dfb4c0b0030b3dbc1e1c2` changes just the
  parameterized test expectation in
  `tests/test_synthetic_mock_cold_restart_boundaries_run643.py`
  from 0 to 1 for `after_mock_marker`. No code semantics, crash ordering,
  schema, or safety gates were relaxed.
- Memory carrier hardening `04e396bf9139f88a90f9be9c0e50e7a05337d2f8`:
  `src/ark/memory/sqlite_event_prefix_review.py` pins original field
  descriptors and class-local `__new__`, `__getattribute__`, `__getattr__`
  hooks for retained witness and comparison classes. The input witness is
  checked *before* any field getter and the comparison object is rechecked
  immediately after its constructor callback before result field reads.
  No Memory DDL, live mutating API, or frozen contract changed.
- Memory field-regression cases `f1d78fd36dbc07077a97da49020b165a5d296882`:
  `tests/test_memory_event_prefix_carrier_preaccess_run644.py` adds
  **9** authored cases: three hostile witness fields; four comparison
  fields; a reentrant comparison digest callback; intact local behavior.
  The tests do not alter inherited Python `__new__` hooks.
- Memory two-handle continuity `7abee38cbffce2795b4c2cbb3e72bc5b03d5b8d8`:
  `tests/test_memory_event_prefix_two_handle_integrity_run644.py`
  adds **4** authored cases (two owners, one historical event rewrite
  after a real local append, one foreign-database same-count witness).
  A valid append may show `ADVANCED_PREFIX_UNAUTHENTICATED` but does not
  prove who wrote it; a stale/foreign prior witness must fail closed.
- Planner competing terminal results `206094e8ecea26d267d8a87f80a6dea47e306de3`:
  `tests/test_planner_competing_terminal_restart_run644.py` adds
  **2** authored cases for simultaneous distinct terminal outcomes
  on one previously RUNNING root. One persisted terminal event must
  win, with one coherent dependent cascade; the loser stays stale.
  Fresh SQLite recovery and deny-only authorization flags are asserted.

**New test cases authored: 15, not a claim of 15 PASS.**
The test expectation correction is separate from that count.
Local `git` cannot resolve github.com; therefore no local pytest or Ruff
execution is claimed. GitHub Actions results must be inspected, and any
failure corrected on the ordinary guarded write path.

## CI observations / validation limits

- Run643 [#42116873087](https://github.com/Iam-2squared/ark-ai/actions/runs/42116873087),
  [#42117034367](https://github.com/Iam-2squared/ark-ai/actions/runs/42117034367),
  and checkpoint [#42117507469](https://github.com/Iam-2squared/ark-ai/actions/runs/42117507469)
  completed **6/6 FAIL**, due to the expected-count test defect described above.
- [Mock fix #42123621367](https://github.com/Iam-2squared/ark-ai/actions/runs/42123621367):
  **IN PROGRESS** at initial read.
- [Memory source #42123821795](https://github.com/Iam-2squared/ark-ai/actions/runs/42123821795):
  **IN PROGRESS** at initial read.
- [Memory field tests #42123928161](https://github.com/Iam-2squared/ark-ai/actions/runs/42123928161):
  **IN PROGRESS** at initial read.
- [Latest source/test #42124289369](https://github.com/Iam-2squared/ark-ai/actions/runs/42124289369):
  **IN PROGRESS** at last pre-repair observation. No latest-head GREEN is claimed.
- **CI regression correction:** Memory-source [#42123821795](https://github.com/Iam-2squared/ark-ai/actions/runs/42123821795)
  and field-test [#42123928161](https://github.com/Iam-2squared/ark-ai/actions/runs/42123928161)
  each showed Ubuntu Python 3.11 **2 FAIL** (source: 9,190 PASS / 1 SKIP;
  tests: 9,199 PASS / 1 SKIP). Existing Run611 tests expected a forged
  `__getattribute__` callback to execute once before refusal; the new
  pre-access guard correctly rejects it **before** the callback executes.
  Test-only semantics-alignment fix
  `bcf4da3f3920881b440e3499403cb1a919b8dd8f`
  updates those two asserted callback counts to zero. The hardened source
  remains unchanged; this is not a claim of GREEN.

The synthetic journals and witnesses offer *local* continuity only. They
cannot prove independent custodianship, consent, trusted time, external
effect exactly-once, atomic commits across independent SQLite databases,
physical-device readiness, V2 final-evaluation clearance or model identity.
An unchanged exact-type local record is not a proof of its origin.

## Frozen limits and next plan / 今後の方針

- PR #5 V3 and PR #9 Next UI remain Draft/unmerged and untouched.
  New UI/frontend development stays paused.
- `main`, frozen V1/V2/Local UI/Launcher and protected V2 final
  evaluation untouched. No real Candidate generation, external GPU,
  paid service, credential/account connection, automatic promotion,
  or manual-approval substitution.
- Next: confirm all six jobs on the exact newest source/test head,
  inspect full logs on FAIL and apply a semantics-preserving fix.
  Then evolve Memory retained/event/row reconciliation, Planner UNKNOWN
  recovery, and disconnected ToolRegistry/PermissionGate/audit-before-
  mock-action with explicit manual triage, not live execution.
