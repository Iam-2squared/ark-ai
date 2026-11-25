# Run1408 — PermissionGate absent class-hook custody

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `36368ccc4160727c79fb24704a675d589575b414`.
- Child branch: `research/run1408-permission-gate-hook-absence-custody-20261125`.
- Child HEAD before this evidence document: `7ec5214af27cd94ae9203b351bfe84b5e0164d30`.
- Source: `src/ark/agency/policy.py`.
- Regression test: `tests/test_permission_gate_hook_absence_custody_run1408.py`.

## Finding

The exact-type PermissionGate guard and its CapabilityGrant, ToolSpec, and OneShotAuthorization validators retained class-hook inventories with `vars(type).get(name)`. For an absent hook this recorded `None`, which is indistinguishable from an explicitly installed class attribute whose value is `None`. The existing aggregate vector-identity checks did not distinguish that namespace-membership change.

## Correction

Each guard now retains a unique absence sentinel in its import-time hook inventory. The captured aggregate epochs include the sentinel identities. Before reading caller fields or spending a local WRITE token, each guard checks:

- exact hook-name vector, descriptor vector, and sentinel identity;
- whether each hook name is actually present in the class namespace;
- exact descriptor identity when the hook is present.

The PermissionGate class itself now receives the same lookup/allocation-hook inventory check as its grant/spec/token input carriers. No new authority is granted.

## Regression coverage

- Explicit `None` for `__new__`, `__getattribute__`, and `__getattr__` is rejected for the gate and all three input carrier types.
- Installing the exact absence sentinel as a hook is rejected.
- Replacing any of the four absence sentinels is rejected.
- Equal-valued replacement hook-name tuples are rejected.
- The original hook inventories remain accepted.
- Every mutation denial occurs before a synthetic WRITE token is consumed.

Tests use only synthetic local ToolCall/ToolSpec/grant/token values and in-memory class monkeypatches. No backend is invoked.

## Scope and evidence limits

PermissionGate public API, grant matching and expiry semantics, registry-bound identity, process-local one-shot behavior, ToolCall v1, ToolRegistry, ActionAudit v1, SQLite schemas, and frozen contracts are unchanged. This is in-process class-definition integrity, not a Python sandbox, durable authorization, trusted-time proof, authenticated consent, or exactly-once external-effect evidence.

No paid/external compute, paid service, Candidate generation/promotion, protected V2 evaluation, credentials, hardware, destructive action, frozen-contract change, main merge, or UI/frontend work occurred. PR #5 and #8 remain Draft/unmerged; PR #9 remains untouched. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no PASS is claimed.
