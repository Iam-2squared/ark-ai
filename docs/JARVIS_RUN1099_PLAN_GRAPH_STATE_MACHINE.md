# Run1099 — Direct PlanGraph state-machine coverage

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`
- Work-basis HEAD: `5aae41319f67cfef8f78b32a9eb6808fd9247ea4`
- Child branch: `research/run1099-plan-graph-state-machine`
- Test: `tests/test_plan_graph_state_machine_run1099.py`

## Change

Adds direct tests for the core `PlanGraph` API rather than relying only on downstream journal and disconnected-recovery fixtures.

Coverage includes:

- Deterministic topology identity independent of registration order while retaining dependency-tuple order.
- Ready-step gating across independent roots, a two-parent join and a leaf.
- Revision-guarded transitions and non-success terminal propagation through a join and its descendants.
- Rejection of terminal resurrection, blocked-step execution and stale revisions without changing the status digest.
- Atomic in-memory publication: a synthetic failure while staging the final descendant must leave every live status/revision unchanged.
- Read-only mapping views and detached status values.
- Exact-type transition ingress, including a hostile `str` subclass and rejection of `bool` as an integer revision.

## Scope and limits

Test-only. No production Planner source, PlanStep/ToolCall contract, persistence schema, authorization, ToolRegistry, PermissionGate, audit, or execution backend changed. The test uses only synthetic local PlanGraph values and monkeypatches the local dataclass-copy function to exercise staging failure. It does not claim durable recovery, trusted time, external-effect atomicity, or permission to dispatch/replay.

## Validation

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS or CI GREEN is claimed.
