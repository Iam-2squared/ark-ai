# Run1237 — ToolRegistry deletion-seal regression

## Exact basis

- Repository: `Iam-2squared/ark-ai`.
- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent HEAD: `36a1c947196efb26a0328b25c516054e80a77536`.
- Child branch: `research/run1237-tool-registry-delete-seal`.
- Test-only change. ToolRegistry implementation, registry revision algorithm, ToolCall contract and V1/V2 freezes are unchanged.

## Coverage

- Ordinary deletion of every sealed ToolRegistry slot is rejected.
- Reflective `object.__delattr__` removal of the registration map fails closed at the public bind boundary before any backend call.
- Replacement of the class-level `__delattr__` guard is detected before registry reads or backend access.
- A healthy registry still binds deterministically while keeping the backend disconnected.

All backends are inert test sentinels. No dispatch, permission grant, one-shot authorization or external action is performed. This is local in-process immutability evidence, not tamper-proofing against arbitrary process memory modification or backend attestation.

No paid/external compute, credentials, hardware, Candidate generation, protected V2 evaluation, UI work, frozen-contract change or main merge. PR #8 remains Draft/unmerged and ARK/JARVIS remains NOT_PASSED. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required.
