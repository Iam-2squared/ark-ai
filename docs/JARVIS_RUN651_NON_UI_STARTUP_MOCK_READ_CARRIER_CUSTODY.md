# ARK AI — Run651 non-UI Startup/Mock READ Carrier Integrity

**Status: SAVED FOUNDATION WORK, NOT ROADMAP PASS.** 2026-11-06 JST. Exact invocation work basis: `b97875efc81214659491471d7a3d5d6291a7ec0e`; branch `research/jarvis-foundations` (Draft PR #8). No UI/frontend changes. All observations here are about disconnected mock computations, not real ToolBackend actions, approved CPU/GPU operations, consent, or external effects.

## 1. Verified incoming CI failure / compatibility repair

The Run650 checkpoint CI [#42156343240](https://github.com/Iam-2squared/ark-ai/actions/runs/42156343240) **FAILED all six jobs** (Ubuntu/Windows, Python 3.11/3.12/3.13). The Ubuntu 3.11 log records **3 FAIL / 9,428 PASS / 1 SKIP**. All three were in `tests/test_startup_exact_requirement_epoch_run419.py`: two old regular-expression assertions expected late `epoch` rejection but the new Run650 original-descriptor guard now rejects earlier with `readiness requirement descriptor changed before review`; one expected `epoch` but receives `readiness result constructor or descriptor changed`. Commit `ec35feaea02e9cc49954793568b305a0d0fbf122` changes the old expectations and explicitly checks that poisoned callbacks never execute. No startup guard was loosened. Its CI [#42158310199](https://github.com/Iam-2squared/ark-ai/actions/runs/42158310199) was IN PROGRESS when last inspected.

## 2. Package B — disconnected toolbox original-carrier custody

Source commit `b36ab9e1da8f26a6fcaa45b8746d3c23f3be5cfa` strengthens `src/ark/agency/disconnected_toolbox.py`. This formerly pinned False-only denial getters but not original request/result dataclass fields or executable constructor and lookup hooks. The new checks compare import-original exact class/slot identities before reading the request's private canonical JSON and again after reentrant fixture/hash callbacks, before constructing/accessing the synthetic result. A correct `math.sum` response remains a local in-memory deterministic **fixture**, with all authority flags False.

New test file `tests/test_disconnected_toolbox_preaccess_carrier_custody_run651.py` covers poisoned request and result fields, constructor and lookup hooks, two mid-calculation mutation boundaries, and one valid deny-only computation. **17 authored cases after correction**. `tests/test_disconnected_tool_result_denials_run585.py` was also updated to expect the correct earlier rejection, asserting the malicious lookup callback is not executed. This is test compatibility, not relaxation.

### Actual CI failure and repair

First new-test CI [#42158581841](https://github.com/Iam-2squared/ark-ai/actions/runs/42158581841) **FAILED all six** due four Ruff B010 usages in the new test; fixed via ordinary Contents commit `2727cdff8747192b15cd67b3aebab14013064580`. Another intermediate run [#42158700673](https://github.com/Iam-2squared/ark-ai/actions/runs/42158700673) showed a **297-FAIL cascade on Ubuntu 3.11**: the test monkeypatched inherited `__new__`, and teardown left the Python class allocator corrupted even after `delattr`. **This is a test-isolation bug, not a discovered production dispatch issue.** The hazardous inherited-`__new__` parameter cases were removed in ordinary commit `6a1cdd1690e3ed9df4986a8e5d725cddefdcba44`. Production checks still validate original `__new__` hooks. The prior Run585 late-error expectation was repaired in `1fb1ab16aca74a358ca19b91db7bd06c27c8f270`. Final six-platform CI remained **UNVERIFIED** at report creation.

## 3. Package C — disconnected READ reference original-carrier custody

Source commit `ce42e52df6d94705da517e0c2f20824fb09cb519` strengthens `src/ark/agency/disconnected_reference_binding.py`. It pins import-original `SyntheticReadResult` and `SyntheticBoundArguments` class identities, exact fields, constructors, lookup hooks and output denial getters before raw result reads and after reference parser/hash/constructor/denial boundaries. Even a correctly resolved synthetic JSON pointer is not tool provenance or authorization.

New `tests/test_disconnected_reference_carriers_run651.py` adds **19 authored regression cases after correction**, covering original carrier/denial hooks, a reentrant JSON-loader constructor substitution, and a positive `{"n":4}` result with all authority flags False. Its inherited-`__new__` poison tests were also removed (commit `03a34a1df797dca5b009b67cc91875c6fc29f15d`) to avoid the same cross-test interpreter contamination. The remaining source-level `__new__` guard is intact.

## Verification / integrity boundaries

- Initial PR #8 HEAD `b97875efc81214659491471d7a3d5d6291a7ec0e`; corrected source/test HEAD before this report `1fb1ab16aca74a358ca19b91db7bd06c27c8f270`. [GitHub compare](https://github.com/Iam-2squared/ark-ai/compare/b97875efc81214659491471d7a3d5d6291a7ec0e...1fb1ab16aca74a358ca19b91db7bd06c27c8f270) showed **9 fast-forward commits / exactly 6 changed paths**, comprising 2 non-UI source changes, 2 new tests and 2 repaired old non-UI tests. No UI or frozen evidence file is among these paths.
- Authored **36** new test cases across B+C (17+19). These numbers are NOT pytest PASS counts; all-six GREEN is NOT established on the repaired exact HEAD until GitHub Actions finishes.
- Corrected-source exact-head [CI #42159188548](https://github.com/Iam-2squared/ark-ai/actions/runs/42159188548) was **QUEUED** on last inspected snapshot. Earlier failing/intermediate CI must never be relabeled GREEN. No duplicate CI runs were requested.
- No local pytest or Ruff was run for this repository (GitHub access was through the normal connector; the local container could not resolve github.com). No change to main, V1/V2/Local UI/Launcher freezes, PR #5 protected V3 Contract, PR #9 UI. No paid APIs, GPU, Candidate adapters/weights, real hardware or ToolBackend execution, protected final V2 evaluation, promotion or explicit-approval merge.
- Class-descriptor fail-closed checks are a **local, reversible fixture-integrity layer**, not a sandbox, authenticated issuer, trusted time, consent, independently retained event witness, or exactly-once external execution.

## Next plan / 今後の方針

1. Inspect corrected exact-head six-job CI when jobs complete, repair only real logged failures; never suppress failing tests or introduce inherited-`__new__` class-slot contamination.
2. Memory COMMIT-UNKNOWN and row/event prefix consistency using retained independent witnesses and non-attribution. Keep ambiguous updates manual-only.
3. Planner restart recovery with RUNNING -> UNKNOWN, no implicit WRITE replay; verify terminal dependency propagation and a persisted audit-before-action mock ordering gate.
4. Connect only mock/disconnected ToolRegistry, exact-type PermissionGate and durable occurrence/audit checks after lower-layer exact-head GREEN. Keep all live tool and UI lanes paused.
