# Run1101 — PermissionGate exact-type and one-shot contract coverage

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`
- Work-basis HEAD: `5aae41319f67cfef8f78b32a9eb6808fd9247ea4`
- Child branch: `research/run1101-permission-gate-one-shot-contract`
- Test: `tests/test_permission_gate_contract_run1101.py`

## Change

Adds direct tests for the local PermissionGate boundary:

- READ authorization requires an active capability grant matching the exact capability and scope.
- Exact expiry boundary and exact integer clock validation are enforced.
- WRITE tokens are bound to the exact request, expired tokens are rejected before local consumption, and a successfully consumed token cannot be reused.
- A reentrant grant generator cannot mutate a previously admitted grant and still reach the token-spend step.
- Two concurrent callers sharing one gate/token produce exactly one local consumption.
- A PermissionGate subclass cannot replace the original gate's token/lock custody.

## Scope and limits

Test-only. No production PermissionGate, frozen ToolSpec/ToolCall/CapabilityGrant/OneShotAuthorization contract, ToolRegistry, durable authorization ledger, audit schema, or executor changed. The one-shot set is process-local and is not restart-safe authorization, human consent, trusted time, or external-effect exactly-once proof. No backend is registered or executed.

## Validation

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS or CI GREEN is claimed.
