# Run1396 — ToolRegistry deletion-seal regressions on current foundation

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `5628f791177668b3c74b6906208b7b92f504ad59`; parent exact-head CI run `45590765382` was GREEN (6/6) before this child was created.
- Rebased from Draft PR #562 / Run1383, whose original child HEAD `8bc8bf974759ca98a9c6be12d0d961716ee654dc` had CI run `45576435715` GREEN (6/6). That prior result does not transfer to this rebased head.
- Verified unchanged ToolRegistry source blob on the parent: `src/ark/agency/registry.py` `2bbb88f6d87a5c51c7b025072e10c998ebc400b9`.
- Child branch: `research/run1396-tool-registry-delete-seal-rebase-20261125`.

## Regression coverage

- Ordinary deletion of every sealed ToolRegistry slot is refused.
- Reflective registration-map deletion is rejected before public binding returns an identity.
- A replaced class-level deletion guard is detected before the replacement executes.
- Healthy deterministic binding remains available; the disconnected mock backend is never invoked.

## Scope and evidence limits

Test/documentation-only. ToolRegistry source, registry contract, ToolCall, PermissionGate, backend binding and dispatch policy are unchanged. These are local in-process object-integrity checks only; they do not establish process isolation, authenticated backend identity, permission, trusted time, durable authorization or exactly-once external effects.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no PASS is claimed before completion. No real backend, device/network I/O, paid/external compute, Candidate, protected V2 evaluation, credentials, hardware, destructive action, frozen-contract change, main merge or UI/frontend work occurred. PR #5/#8 remain Draft/unmerged and PR #9 remains untouched; ARK/JARVIS remains NOT_PASSED.
