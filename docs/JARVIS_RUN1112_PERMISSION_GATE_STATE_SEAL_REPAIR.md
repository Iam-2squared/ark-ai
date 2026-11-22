# ARK Run1112 — PermissionGate slot-state compatibility repair

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent HEAD: `6bdbe12acadc2ffa5c7506c4e8d9b41b722f7e83`.
- Original state-seal child: Draft PR #279, exact failed CI head `92e7098042a639b4facab1da9a291af93607d912`.
- Repair branch: `research/run1112-permission-gate-state-seal-repair`.
- Repair work-basis HEAD before this report: `abd43385c7a35aea290abfdee010c7d4e34dbfd6`.

## Failure evidence and root causes

Original child CI [#45025219785](https://github.com/Iam-2squared/ark-ai/actions/runs/45025219785) failed on all six matrix jobs: 55 failures, 19,241 passed, 1 skipped. The failure was not a single policy assertion:

1. Subclass construction reached overridden `__getattribute__` before the exact-type denial.
2. The disconnected mock executor called `vars(gate)` (and `vars(registry)`) on newly slot-only objects, raising `TypeError`.
3. Older fault-injection tests attempted ordinary replacement of the now-sealed token/lock state or instance methods. Several spend-race tests substituted the lock itself, which the new state-identity guard correctly rejects before the lock callback.

## Repair

- Check exact `PermissionGate` type at the start of `__init__`, before any instance attribute access.
- Preserve the established “implementation identity changed” diagnostic when the class contract is replaced.
- Make disconnected executor namespace inspection tolerate exact slot-only registry/gate instances; exact types are checked before namespace inspection.
- Rewrite concurrency regressions to hold the original gate lock while a worker reaches the spend boundary, then mutate only the synthetic grant/spec/registration carriers. This preserves the intended post-wait revalidation test without replacing lock custody.
- Replace tests that attempted ordinary mutation of sealed token state or instance methods with explicit denial assertions. Token replacement remains denied; ordinary method shadow assignment is denied; replay remains rejected.

No gate, token, lock, grant, registry, executor, audit, or dispatch authority is broadened. No real backend is called.

## Validation boundary

The original run is **FAIL** and applies only to its exact old child head. This repair has not been locally executed; fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required after the repair PR is opened. No test PASS is claimed here.

PermissionGate token spending remains process-local, not durable consent or trusted-clock approval. The disconnected executor remains a fixture-only boundary; this does not prove independent actor provenance, cross-store atomicity, real-world execution, or exactly-once external effects. PR #5 and PR #8 remain Draft/unmerged; UI remains paused. No paid service, external compute, Candidate, protected evaluation, credentials, physical hardware, frozen-contract change, or main merge.
