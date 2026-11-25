# Run1419 — ToolRegistry allocation and lookup-hook absence custody

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD for this rebase: `a1bff14b0ca731ee1d094d6611caf76c08640398`.
- Original source package: Draft PR #601 / Run1419, based on `996d557f6b723229ffc201ac827b8a908e90a7ae`.
- Verified parent source blob before reapplication: `4e1d1edf54ba383cceed87013c50c40a0d13232e`, identical at the old source base and the exact current parent.
- New child branch: `research/run1423-registry-hook-custody-20261126`.
- Child HEAD immediately before this evidence correction: `0598e8a48e6276261bce8356a0b4513f9c834865`.
- Source: `src/ark/agency/registry.py`.
- Regression test: `tests/test_tool_registry_absent_hook_custody_run1419.py`.

## Finding and correction

The exact ToolRegistry instance seal pinned its slot layout and assignment/deletion descriptors, but did not pin allocation and lookup hooks. A missing `__new__`, `__getattribute__` or `__getattr__` namespace entry could therefore be replaced with explicit `None` without being distinguished from true absence. The guard also did not retain the constructor descriptor in its class epoch.

The rebase preserves the current parent source and adds a unique absent-hook sentinel plus one retained class epoch covering the import-original class, public alias, slot layout, assignment/deletion descriptors, constructor descriptor, hook-name/original-hook vectors and sentinel. The guard checks the epoch and module aliases before inspecting the retained original class namespace. Expected-absent hooks require namespace non-membership; expected-present descriptors require exact identity.

## Regression coverage

- Explicit `None` and exact-sentinel installation are rejected for `__new__`, `__getattribute__` and `__getattr__`.
- Hook-name/original-hook vectors, sentinel, epoch, class aliases and constructor identity replacement are rejected.
- A hostile lookup hook is rejected by a static registry entrypoint before instance-state access.
- All registrations use an inert backend; no backend dispatch is permitted.

## Evidence limits and hard stops

This is in-process class-definition integrity only. It is not a Python sandbox, independent custody, authenticated consent, trusted time, durable authorization or exactly-once external-effect evidence. It does not authorize ToolBackend execution. ToolRegistry public APIs, registration ordering, revision digest, bound-action identity, mapping semantics, ToolCall v1, PermissionGate contract, SQLite schemas and frozen evidence are unchanged.

No paid/external compute or service, Candidate generation/promotion, protected V2 evaluation, credentials/account connection, hardware action, destructive operation, main write/merge or UI/frontend work occurred. PR #8 remains Draft/unmerged; PR #5 remains gated Draft/unmerged; PR #9 remains untouched.

The original PR #601 run `45669883259` was GREEN 6/6 on its older child head only. It does not transfer. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required for this rebase. No local pytest/Ruff result or PASS is claimed.