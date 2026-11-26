# Run992 — Planner / ToolRegistry preflight

## Scope and basis

- Repository: Iam-2squared/ark-ai
- Isolated branch: research/plan-registry-preflight-run992
- Exact base: Draft PR #8 head 326001af654078227641546a8f30c6954fcea4a3
- Module: src/ark/agency/plan_registry_preflight.py
- Tests: tests/test_plan_registry_preflight_run992.py
- This is a read-only adapter. It does not change PlanGraph, ToolRegistry, frozen contracts, production dispatch, or UI code.

## Behavior

The adapter binds every PlanStep ToolCall against one immutable ToolRegistry revision. It records only bounded identities:

- plan topology digest
- plan status digest
- registry revision
- currently ready step IDs
- per-step tool name, capability, effect, backend ID, request ID and bound action ID
- a domain-separated local fingerprint

The plan and registry epochs are checked before and after each binding and again before returning the result. Unknown or mismatched tools fail the whole preflight. The adapter never invokes a backend method, grants permission, advances a PlanGraph state, or creates a runnable queue.

All result authority properties are explicitly false: permission granted, dispatch authorized, tool execution authorized, automatic replay authorized, trusted clock verified and consent verified.

## Regression coverage authored

Five synthetic cases cover:

1. Valid two-step dependency graph binds both steps to one registry revision; only the root is currently ready.
2. Unknown plan tool rejects the whole preflight without backend execution.
3. Instance-shadowed ToolRegistry binding method is rejected before it runs.
4. A PlanGraph status transition changes the status digest, ready set and fingerprint without dispatch.
5. Replaced PlanGraph status-digest method is rejected before preflight.

A no-dispatch backend fixture raises if its execute method is ever called. Exact-head CI is required before treating these tests as validated.

## Limitations

- A registry binding is not a PermissionGate grant.
- A ready step is not permission to run.
- Registry revision and digests are process-local consistency witnesses, not authenticated provenance.
- The preflight is not a durable Planner journal or crash-recovery mechanism.
- It does not establish a trusted clock, user consent, external effect, exactly-once execution or automatic replay.
- Backend identities are local registry metadata, not remote attestation.

## Frozen boundaries

V1/V2, Local UI, Launcher, PlanStep/ToolCall, Memory v1, Observation Envelope v1 and V3 Contract 1 remain unchanged. PR #5 remains gated Draft/unmerged. PR #9 remains paused and untouched. No paid service, external compute, Candidate, protected V2 evaluation, credentials, physical hardware, real tool dispatch or main merge is involved.

Overall ARK/JARVIS remains NOT_PASSED.
