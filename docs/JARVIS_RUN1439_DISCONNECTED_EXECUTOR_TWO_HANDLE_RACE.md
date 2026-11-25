# Run1439 — disconnected mock executor two-handle WRITE race

## Exact basis

- Parent: Draft PR #8, branch \`research/jarvis-foundations\`.
- Exact parent work-basis HEAD: \`5a344d250dd0ef2a208ccd09f5d791b10c548bbe\`.
- Child branch: \`research/run1439-disconnected-executor-two-handle-race-20261126\`.
- Regression test: \`tests/test_disconnected_mock_executor_two_handle_race_run1439.py\`.

## Finding and coverage

The durable occurrence store already has independent two-handle reservation race coverage, and the disconnected executor already has restart and hard-exit coverage. This package closes the composition-level gap: two separate executor instances, each with its own process-local PermissionGate and SQLite occurrence handle, race the same WRITE request, one-shot token and occurrence ID.

The test requires exactly one durable reservation, one actual gate consumption, one mock backend call, and exactly one pre-action/completion audit pair. The losing executor must fail at durable reservation before consuming its gate or dispatching the mock.

## Boundaries

- Test-only change; no production source, schema, DDL, ToolCall, PermissionGate or frozen contract changes.
- Exact in-process \`MockToolBackend\` only. No external backend, shell, network, device, model, notification or real action.
- Caller time/token are synthetic and unauthenticated. A single local reservation is not trusted consent, trusted-clock evidence, independent custody, or proof of exactly-once external effects.
- Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff result is claimed.

No paid/external compute, credentials, hardware, destructive operation, main write/merge, V3 preflight/training, protected evaluation, Candidate action, or UI/frontend work occurred. PR #8 remains Draft/unmerged; PR #9 remains untouched.
