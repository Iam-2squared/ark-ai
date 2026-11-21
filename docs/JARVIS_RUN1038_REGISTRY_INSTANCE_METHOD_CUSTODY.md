# Run1038 — ToolRegistry instance-method custody at registered authorization

## Exact work basis

- Parent: Draft PR #8, branch research/jarvis-foundations.
- Exact parent HEAD: 784f93d7a48860e774f6d94648ff4e44297c9569.
- Source: src/ark/agency/policy.py.
- Regression: tests/test_permission_gate_registry_instance_method_custody_run1038.py.
- This is a local policy/identity guard. It does not dispatch a backend or create durable user approval.

## Finding

ToolRegistry is an exact class instance but has an instance dictionary. Its public bind, resolve, get and internal epoch methods can therefore be shadowed on one instance. PermissionGate.authorize_registered pinned class-level bind/resolve/revision descriptors, but did not statically verify the corresponding instance descriptors. It also only pinned class-level bind when a one-shot token was present, even though READ authorization also relies on registry-bound identity.

A shadowed bind could return the same forged BoundAction twice, pass the old bound-versus-verified equality check, and supply a registration identity that was not produced by the original registry implementation.

## Change

- Pin ToolRegistry get, registrations, epoch and revision-computation descriptors at import time.
- Before every registered-authorization boundary, compare both class and instance static descriptors for bind, resolve, get, revision, registrations, _assert_registration_epoch and _compute_revision.
- Apply the bind identity check to READ and WRITE alike.
- Invoke the captured original unbound bind implementation after descriptor custody is established, rather than dispatching through a potentially shadowed instance attribute.
- Recheck the descriptor set after grant-iterator callbacks and before token admission.

## Regression coverage

Synthetic tests attempt instance shadows for bind, resolve, get, _assert_registration_epoch and _compute_revision; attempt a class-level bind replacement on a READ request; and mutate registry.get from a grant generator after initial binding. Each case requires PermissionDenied before a shadowed callback or grant iteration can run, with no token spend and no backend dispatch.

## Limits and frozen boundaries

This remains an in-process identity/drift check, not a security sandbox against arbitrary memory rewriting, a trusted runtime identity, a durable authorization receipt, a trusted clock, or exactly-once external execution. ToolRegistry's existing data and contract remain unchanged. No V1/V2, Local UI/Launcher, PR #5, PR #9, main, evaluation gate, Candidate, or external service is changed or opened.


## CI repair note

The first exact-head CI attempt exposed 29 legacy assertions that intentionally installed instance-shadowed registry methods as callback injectors. The new custody check correctly rejects those shadows before invoking them, so those tests could no longer use that forbidden callback path to mutate grants/actions/tokens. The test harnesses were revised to keep reentrant action/token/grant epoch coverage on the supported grant-iterator callback boundary, and to assert that registry method shadows are denied before invocation, grant iteration or token spend. This is a stronger early-denial assertion, not a relaxed policy gate. The failed run remains historical; fresh exact-head CI is required and no PASS is transferred.
