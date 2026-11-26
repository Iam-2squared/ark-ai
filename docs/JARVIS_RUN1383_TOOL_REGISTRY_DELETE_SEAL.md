# Run1383 — ToolRegistry deletion-seal regressions on the current foundation

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `11d72bef1b69df06ed0c0102d6154fc4d44a0214`.
- Child PR: Draft #562, branch `research/run1383-tool-registry-delete-seal-rebase-20261125`.
- Child test commit before this evidence document: `3267ae1b8cb2c89fb5393b6cc652a4a7a4266873`.
- Verified unchanged ToolRegistry source blob: `src/ark/agency/registry.py` `2bbb88f6d87a5c51c7b025072e10c998ebc400b9`.
- Exact-head CI run `45576384507` was queued when this document was written; previous child CI does not transfer.

## Regression coverage

- Ordinary deletion of every sealed ToolRegistry slot is refused.
- Reflective registration-map deletion is rejected before public binding returns an identity.
- A replaced class-level deletion guard is detected before the replacement executes.
- Healthy deterministic binding remains available; the disconnected mock backend is never invoked.

## Scope and evidence boundary

Test/documentation-only. ToolRegistry source, registry contract, ToolCall, PermissionGate, backend binding and dispatch policy are unchanged. These are local in-process object-integrity checks, not process isolation, authenticated backend identity, permission, trusted time, durable authorization or exactly-once external-effect evidence.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no PASS is claimed until it completes. No real backend, device/network I/O, paid/external compute, Candidate, protected V2 evaluation, credentials, hardware, destructive action, frozen-contract change, main merge or UI/frontend work occurred. PR #5/#8/#9 remain under their existing gates; ARK/JARVIS remains NOT_PASSED.
