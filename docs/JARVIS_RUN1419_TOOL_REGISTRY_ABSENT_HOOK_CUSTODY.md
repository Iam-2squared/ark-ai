# Run1419 — ToolRegistry allocation and lookup-hook absence custody

## Exact basis

- Parent: Draft PR #8, branch \`research/jarvis-foundations\`.
- Exact parent work-basis HEAD: \`996d557f6b723229ffc201ac827b8a908e90a7ae\`.
- Child branch: \`research/run1419-tool-registry-absent-hook-custody-20261126\`.
- Source: \`src/ark/agency/registry.py\`.
- Regression test: \`tests/test_tool_registry_absent_hook_custody_run1419.py\`.

## Finding

The exact ToolRegistry instance seal pinned its slot layout and assignment/deletion descriptors, but did not pin allocation and lookup hooks. A missing \`__new__\`, \`__getattribute__\` or \`__getattr__\` namespace entry could therefore be replaced with explicit \`None\` without being distinguished from true absence by the existing class guard. The guard also did not retain the constructor descriptor in its class epoch.

## Change

- Capture a unique absent-hook sentinel and the exact hook-name/original-hook vectors.
- Retain the import-original class, public alias, slot layout, assignment/deletion descriptors, constructor descriptor, hook vectors and sentinel in one epoch.
- Check epoch and module-alias identity before inspecting the namespace of the retained original class.
- Require namespace non-membership for sentinel-backed absent hooks and exact descriptor identity for present hooks.
- Keep ToolRegistry public APIs, registration ordering, revision digest, bound-action identity, mapping semantics and backend behavior unchanged.

## Regression coverage

- Explicit \`None\` and exact-sentinel installation are rejected for \`__new__\`, \`__getattribute__\` and \`__getattr__\`.
- Hook-name/original-hook vectors, sentinel, epoch, class aliases and constructor identity replacement are rejected.
- A hostile lookup hook is rejected by a static registry entrypoint before the instance-state callback can execute.
- All registrations use an inert backend; no backend dispatch is permitted.

## Evidence limits and hard stops

This is in-process class-definition integrity only. It is not a Python sandbox, independent custody, authenticated consent, trusted time, durable authorization or exactly-once external-effect evidence. It does not authorize any ToolBackend execution. No ToolCall v1, PermissionGate contract, registry revision digest, SQLite schema, frozen contract or V1/V2 evidence is changed.

No paid/external compute or service, Candidate generation/promotion, protected V2 evaluation, credentials/account connection, hardware action, destructive operation, main write/merge or UI/frontend work occurred. PR #8 remains Draft/unmerged; PR #5 remains gated Draft/unmerged; PR #9 remains untouched.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required after the child PR is opened. No local pytest/Ruff result or PASS is claimed.
