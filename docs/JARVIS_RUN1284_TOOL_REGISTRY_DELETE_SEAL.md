# ARK Run1284 — ToolRegistry deletion-seal regression

## Exact basis

- Repository: `Iam-2squared/ark-ai`.
- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `101be0cb505d8ae045027faf54f8d982c0a4f9d2`.
- Child branch: `research/run1293-tool-registry-delete-seal-rebase-20261124`.
- Test-only rebase of the ToolRegistry deletion-seal regression previously carried by Draft PR #447.
- The current `src/ark/agency/registry.py` implementation was inspected before the test was copied; the expected deletion guard and contract-change denial are present.

## Regression coverage

- Ordinary deletion of each sealed registry state slot is refused.
- Reflective `object.__delattr__` removal of the registration map is rejected by the public `bind` path before backend access.
- Replacing the class-level `__delattr__` guard is detected before the substituted guard executes.
- A healthy deterministic binding remains usable; the inert backend is never called.

## Evidence boundary

This verifies local in-process ToolRegistry object-integrity behavior only. It does not establish process isolation, authenticated backend identity, permission, trusted time, durable authorization or exactly-once external effects. The fixture is synthetic and never dispatches.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no PASS is claimed before that run completes. No ToolRegistry source, identity algorithm, ToolCall/PermissionGate contract, dispatch path, schema, frozen contract, V1/V2 evidence, UI/frontend work or main branch is changed. No paid/external compute, Candidate, protected V2 evaluation, credentials, hardware or destructive action is used. PR #5/#8/#9 remain under their existing gates; ARK/JARVIS remains NOT_PASSED.
