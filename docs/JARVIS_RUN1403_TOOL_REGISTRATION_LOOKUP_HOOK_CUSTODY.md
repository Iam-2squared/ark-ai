# Run1403 — ToolRegistration lookup-hook custody

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `36368ccc4160727c79fb24704a675d589575b414`.
- Child branch: `research/run1403-tool-registration-lookup-hook-custody-20261125`.
- Child HEAD before this evidence document: `c9e7b9c3c787fc05cbc63634aaebfe5fed8745a6`.
- Source file: `src/ark/agency/registry.py`.
- Source blob after the implementation commit: `4e1d1edf54ba383cceed87013c50c40a0d13232e`.

## Finding and correction

The exact `ToolRegistration` class guard retained `__new__`, `__getattribute__` and `__getattr__` values with `vars(type).get(name)`. For an absent hook, this returns `None`; an explicitly installed `None` therefore compared equal to absence. The guard could accept a changed class lookup policy even though the hook name had become present in the class namespace.

The guard now retains a unique absence sentinel, captures the original class/hook vector/sentinel in keyword-only defaults, and checks both namespace membership and descriptor identity. Explicit `None`, the exact absence sentinel, sentinel replacement and equal-valued hook-vector replacement fail closed before registration fields are read.

## Regression coverage

- Each of `__new__`, `__getattribute__` and `__getattr__` explicitly set to `None` is rejected.
- A hook set to the exact absence sentinel is rejected.
- Replacing the absence sentinel is rejected.
- An equal-valued replacement hook-name tuple is rejected.
- The exact original registration class remains accepted.

All tests use one inert synthetic backend. No backend method is invoked and no permission token is issued or consumed.

## Scope and evidence limits

This is local in-process class/descriptor identity hardening only. It is not a process sandbox, authenticated backend attestation, durable authorization, trusted time, restart-safe exactly-once execution or external-effect authority. ToolRegistry revision/bound-identity formats, ToolCall/ToolSpec contracts, registration semantics and frozen contracts are unchanged.

No live user data, real dispatch, credentials, hardware, paid/external compute, Candidate generation/promotion, protected V2 evaluation, frozen-contract change, main write/merge or UI/frontend work occurred. PR #5/#8/#9 remain under their existing gates. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no PASS is claimed.
