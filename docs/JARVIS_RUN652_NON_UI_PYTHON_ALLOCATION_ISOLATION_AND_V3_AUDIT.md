# ARK AI Run652 — non-UI Python allocation-test isolation and V3 boundary audit

## Basis and scope

- Work-basis PR #8 Draft HEAD: `7fda6994b94377f7c9b3999f6fed50509787cc4d`, from Run651. All development remains on `research/jarvis-foundations`; no changes to UI, main, PR #5 or PR #9.
- Ordinary GitHub Contents commits: `3c00acdedbc7d4f45a36a2c0bdd05bd38f7a53df`, `12be2ffbaf376e16a6ae2b7c9cc512477d7ebeeb`, `cb9cc7ea320a266852f8583270142a6a341f9c8b`.
- All tests remain disconnected/local-only, no paid APIs, external GPU, Candidate production, real tool execution or protected evaluation.

## Root-cause analysis grounded in actual CI logs

[Run651 checkpoint CI #42159582101](https://github.com/Iam-2squared/ark-ai/actions/runs/42159582101) completed with **6/6 job failures**. The Ubuntu 3.11 job `127701786674` includes a first broad failure in `test_legitimate_disconnected_calculation_still_has_no_authority`: `DisconnectedToolResult(...)` raises `TypeError: object.__new__() takes exactly one argument (the type to instantiate)`. Hundreds of later unrelated tests cascade, including registered READ fixtures. This is test-interpreter contamination, not evidence of actual tool dispatch.

The Run651 test file still parameterized `DisconnectedToolResult.__new__` in a parent-process descriptor poison fixture. Deleting the newly set `__new__` after testing does **not** restore the CPython allocation slot's prior behavior. A standalone local dataclass reproducer confirms that a frozen, slotted dataclass can fail construction after an inherited `__new__` has been overridden then deleted.

## Changes

1. Remove the unsafe in-process `__new__` parameter and restore its security assertion **inside a separate child Python process**: a substituted `DisconnectedToolResult.__new__` is rejected before the substitute executes. The subprocess lifetime fences CPython class allocation side effects from the rest of pytest. Also fix the child's script literal after verifying the committed file. The other 14 descriptor/constructor carrier cases remain intact.
2. Independent non-UI file `tests/test_disconnected_reference_new_hook_process_isolation_run652.py` adds **2** isolated child-process regression cases for synthetic READ input and bound-output allocation hooks. They validate early fail-closed denial and zero poisoned callback invocation.
3. Read-only V3 guard audit of [pre-paid-compute gate](https://github.com/Iam-2squared/ark-ai/blob/805b377697472268db02650a89c7a94b1c5337c8/docs/v3/PRE_PAID_COMPUTE_GATE.md), [frozen V3 contract](https://github.com/Iam-2squared/ark-ai/blob/805b377697472268db02650a89c7a94b1c5337c8/docs/v3/CONTRACT.md), and [HF identity review](https://github.com/Iam-2squared/ark-ai/blob/805b377697472268db02650a89c7a94b1c5337c8/docs/v3/HF_IDENTITY_REVIEW.md): no immutable HF revision or actual local snapshot identities supplied; human-reviewed 120/30 provenance/contamination rights, exact runtime/hardware pins, explicit preflight budget/authorization and later distinct training authorization remain unresolved. No V3 gate was opened, no frozen contract modified.

## Test / CI custody and limitation

- Baseline CI **#42159582101**, `7fda699...`: **FAIL 6/6**, first broad allocation failure described above.
- Isolated toolbox regression CI **#42164567476**, `3c00acde...`: **IN PROGRESS** at last read. Its child-script string contained an accidental double backslash; this was corrected in the next ordinary commit, so it does not establish success.
- Fixed child-script CI **#42164693743**, `12be2ffb...`: **IN PROGRESS** at last read.
- Independent READ hook tests CI **#42164800792**, `cb9cc7ea...`: **IN PROGRESS** at last read. Do **not** claim these new tests PASS or current 6/6 GREEN before all jobs report success.
- Local full-suite verification could not be run in this environment: attempted public GitHub clone could not resolve github.com. Do not infer exact-head local pytest or Ruff results.
- These checks are guards for synthetic Python objects in a non-privileged fixture interpreter, not a sandbox, OS protection, authenticated provenance, human consent, trusted clock or permission to replay ambiguous writes.

## Next plan

1. Establish all-six exact-HEAD GREEN by inspecting actual jobs; repair any remaining failing tests through normal GitHub safety path without mutating production safety policy to accommodate older expectations.
2. Once lower-level evidence is GREEN, advance Memory COMMIT-UNKNOWN, retained event history and CAS expiry/ABA correctness with regression tests, then Planner crash-recovery terminal propagation.
3. Connect registry-bound PermissionGate, durable write occurrence, audit-before-action and disconnected mock execution only under lower-level exact-head GREEN.
4. Continue backend privacy/observation/proactive lanes independently; UI stays paused and PR #5/#8/#9 remain Draft/unmerged.
