# Run1100 — Direct ToolRegistry contract coverage

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`
- Work-basis HEAD: `5aae41319f67cfef8f78b32a9eb6808fd9247ea4`
- Child branch: `research/run1100-tool-registry-core-contract`
- Test: `tests/test_tool_registry_core_contract_run1100.py`

## Change

Adds direct tests for the immutable ToolRegistry boundary:

- Registration-order-independent revision identity and a read-only registration map.
- Revision changes when the declared backend identity changes.
- BoundAction identity is stable for the same exact ToolCall and differs for a changed request payload.
- Registry binding and resolution remain inert; synthetic backends are never called.
- Generator resumption cannot mutate an earlier registration after it has been admitted.
- An equal-valued replacement of the registry map is rejected, and ToolCall subclasses are refused at both resolve and bind ingress.

## Scope and limits

Test-only. No production registry, frozen ToolCall/ToolRegistration contract, PermissionGate, authorization ledger, audit schema, or executor changed. The tests establish local in-process identity checks only; a registry revision is not backend attestation, authorization, consent, or proof of an external effect.

## Validation

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS or CI GREEN is claimed.
