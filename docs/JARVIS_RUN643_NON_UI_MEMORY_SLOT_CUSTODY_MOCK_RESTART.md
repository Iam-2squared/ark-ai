# Run643 — Non-UI Memory, WRITE-slot custody, mock crash boundaries

This report records code and tests on **Draft PR #8**; it is not a JARVIS,
V3, external-execution, user-consent, or hardware PASS. No UI changes.

## Exact work basis and saved packages

- Initial work-basis PR HEAD: `0302f272e76f9e75ac5bdfaf9b3c674a85fc2f81`.
  [CI #42106714123](https://github.com/Iam-2squared/ark-ai/actions/runs/42106714123)
  subsequently confirmed **six of six GREEN**.
- **Memory: independent SQLite COMMIT-UNKNOWN lifecycle**, commit
  `8c83f68c7470bd4b3e7e6c4f9e6c531ddbc51e93`;
  `tests/test_memory_commit_unknown_two_handle_lifecycle_run643.py`.
  Five parametrized test cases model an unchanged retained prefix, a different
  handle producing an identical row image, two subsequent updates, and
  deletion/recreation. Local reconciliation is read-only and never attributes
  an ambiguous COMMIT to the requesting writer or approves a retry.
- **Durable synthetic WRITE-slot input carrier preflight**, source commit
  `8d54f7ba54804e8cdc728cc4d62e5c84e4238f45`;
  `src/ark/agency/disconnected_write_slot_ledger.py`.
  In addition to pre-existing constructor/denial checks, the originally
  imported `DetachedWriteSlotClaim` and `WriteSlotLedgerWitness` field
  descriptors and `__new__`/`__getattribute__`/`__getattr__` hooks
  are verified with class-dictionary inspection before reading caller-owned
  carriers or acquiring a WRITE transaction. The checks are repeated through
  existing `_require_original_constructors()` boundaries. No schema,
  reservation algorithm, real dispatch, or frozen contract was changed.
- **Slot pre-access regressions**, commit
  `d832bb8b1ab516f6c9df400768d31581138e32ab`;
  `tests/test_write_slot_preaccess_carriers_run643.py`.
  Thirteen cases require untrusted field and directly defined lookup replacements to
  be refused without executing injected getters or inserting reservation rows,
  including a mutation triggered inside row hashing; intact original carriers
  still permit only a synthetic local reservation.
- **Synthetic mock WRITE cold-restart boundaries**, commit
  `a257e916ddb46cee8b311496de2bb4d7cf91b01e`;
  `tests/test_synthetic_mock_cold_restart_boundaries_run643.py`.
  Six cases reopen separate local Planner/occurrence/audit/link databases after
  each of five fault-injection checkpoints or a completed local mock marker.
  Recovery must preserve UNKNOWN/non-retry and the observed durable sidecar
  tips. It never calls a ToolBackend.

**Newly authored test cases:** 27 (5 Memory + 13 slot custody +
6 mock cold restart + 3 registry/policy replay).
These are counts of test cases, **not evidence of 27 PASS**.

## CI evidence at report preparation

- [#42115004351](https://github.com/Iam-2squared/ark-ai/actions/runs/42115004351)
  on Memory test commit: Ubuntu Python 3.11–3.13 **3/3 GREEN**;
  Windows jobs were IN PROGRESS at observation.
- [#42115413713](https://github.com/Iam-2squared/ark-ai/actions/runs/42115413713)
  on WRITE-slot source commit: Ubuntu **3/3 GREEN**;
  Windows jobs were IN PROGRESS.
- [#42115529509](https://github.com/Iam-2squared/ark-ai/actions/runs/42115529509)
  on WRITE-slot tests: Ubuntu Python 3.11 **9,156 PASS, 33 FAIL,
  1 SKIP**. The test's temporary patch to an inherited
  `__new__` method was restored as a class-local `object.__new__`,
  which polluted subsequent tests and triggered constructor TypeErrors.
  We removed inherited special-method patch cases through the normal
  test-only fix `ffa4a7645b4885dfa04cb738887bdc2fde138306`,
  preserving source preflight checks. This is not evidence of code PASS.
- [#42115777989](https://github.com/Iam-2squared/ark-ai/actions/runs/42115777989)
  inherited the same test pollution; Ubuntu 3/3 FAIL.
- **Fourth package — registry/policy restart replay separation**:
  `tests/test_registry_policy_durable_occurrence_restart_run643.py`
  at `95eff519f15e6c638b1be54f3389c153335e1f10`.
  Three test cases model process-local grants, durable SQLite uniqueness
  across reopened handles, and denied exact-scope admission without backend
  execution. [#42116418782](https://github.com/Iam-2squared/ark-ai/actions/runs/42116418782)
  initially failed Ruff **E501** on a single too-long parametrization line;
  fixed with a formatting-only edit at
  `e1f9981a7e95475de144ee6f7dc1572bed770a38`.
- Latest corrected source/test CI is newly pending; **exact-head 6/6
  GREEN is not yet claimed**.
- Local `git` access failed DNS resolution for `github.com`; therefore no
  local pytest or Ruff claim. CI logs must be inspected if the new head fails.
  Do not rerun equivalent GitHub workflows unnecessarily.

## Trust boundary and remaining limits

These tests and fixes protect *local, disconnected* pre-access and crash
semantics. A patched in-process runtime, SQLite writes, hash witnesses,
application clock, or simulated backend cannot authenticate human permission,
OS identity, trusted time, external side effects, cross-DB atomicity, a real
exactly-once guarantee, or Candidate model identity. Reflected class mutation
is tested only as bounded synthetic fault injection; it is not an adversarial
host-process security boundary.

No UI/frontend, frozen V1/V2/Local UI/Launcher contract, main, PR #5 or #9,
protected final V2 evaluation, real model/Candidate training, account/credential,
external service, physical machine, tool backend execution, or paid compute
was modified or invoked. Keep PR #5/#8/#9 Draft and unmerged.

## Next plan / 今後の方針

1. Confirm **all six** jobs at the exact corrected source/test HEAD,
   inspect logs and use the minimum normal-path fix if any FAIL.
2. Expand Planner's persisted UNKNOWN/terminal recovery and Memory
   event-prefix/CAS manual attribution evidence under concurrent writers.
3. After exact-head tests GREEN, combine registry-bound identity,
   PermissionGate, durable one-shot reservation and audit-before-action in
   another disconnected fixture without any live effect.
4. Continue privacy-safe Personal Context, proactive scheduler/readiness,
   observation input fixtures and read-only V3 free-only approval guard audit.
