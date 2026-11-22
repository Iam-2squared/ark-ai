# Run1102 — startup readiness lease guard-vector regression coverage

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`
- Work-basis HEAD: `e8761e183094cd27955423844a8db7d6b0063829`
- Child branch: `research/run1102-startup-lease-guard-vectors`
- Test: `tests/test_startup_readiness_lease_guard_vectors_run1102.py`

## Change

Adds 40 synthetic regression cases around the existing disconnected startup lease reviewer:

- All 11 descriptor/original-carrier guard vectors reject both empty and equal-valued replacement before any requirement field access.
- Replaced requirement descriptors and startup-authority denial properties fail closed before their poisoned getters execute.
- Component/schema labels reject NUL, line controls, C1 and Unicode formatting controls, invalid UTF-8 surrogate data, and UTF-8 byte-budget overflow.
- The 512-requirement ceiling and exact bounded age input are exercised.

Production readiness code, startup snapshot semantics, schema, V1/V2 contracts, Planner, ToolRegistry, PermissionGate, audit, authorization and executor code are unchanged.

## Limits

This remains a disconnected synthetic diagnostic. A READY lease is not a real startup attestation, trusted clock, human consent, notification permission, dispatch permission, device check, or backend authorization. No local files, devices, credentials, live personal data, or ToolBackend are opened or executed.

## Validation

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed.
