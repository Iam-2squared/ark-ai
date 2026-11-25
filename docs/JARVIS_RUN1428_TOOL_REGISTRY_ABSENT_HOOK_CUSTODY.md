# Run1428 — ToolRegistry absent class-hook custody on latest foundation

## Exact basis

- Parent Draft PR #8 branch: `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `c6ee53c5e5671b926b7625da7a7b5dfdd41ae7d3`.
- Rebased from Draft PR #612, branch `research/run1423-registry-hook-custody-20261126`, exact child HEAD `64af590311be5d74a9f03cc7eedfb8b494f08c7b`.
- Parent source blob before reapplication: `4e1d1edf54ba383cceed87013c50c40a0d13232e`; it matches the source base used by the prior child.
- Reapplied source: `src/ark/agency/registry.py`; regression module: `tests/test_tool_registry_absent_hook_custody_run1419.py`.

## Change

Retains a unique absent-hook sentinel and class-definition epoch covering the original ToolRegistry class and public aliases, slot layout, assignment/deletion descriptors, constructor, hook-name/original-hook vectors, and sentinel. The guard validates aliases and epoch before inspecting the retained original class namespace. Sentinel-backed hooks require true namespace absence; present hooks require exact descriptor identity.

## Regression coverage

- Explicit `None` and exact-sentinel installation are rejected for `__new__`, `__getattribute__`, and `__getattr__`.
- Hook vectors, sentinel, epoch, class aliases, and constructor replacement are rejected.
- A hostile lookup hook is denied by a static registry entrypoint before instance-state access.
- Registrations use an inert backend; no dispatch occurs.

## Scope and evidence limits

ToolRegistry public APIs, registration order, revision digest, bound-action identity, PermissionGate, ToolCall v1, SQLite schemas, and frozen contracts are unchanged. This is in-process class-definition integrity only—not a Python sandbox, independent custody, consent, trusted time, durable authorization, or exactly-once external-effect evidence. It does not authorize ToolBackend execution.

No live data, credentials, hardware, paid/external compute, Candidate generation/promotion, protected V2 evaluation, frozen-contract change, main write/merge, or UI/frontend work occurred. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no production-readiness or ARK/JARVIS PASS is claimed.
