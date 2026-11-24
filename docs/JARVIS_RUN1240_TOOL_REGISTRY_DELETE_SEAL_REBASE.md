# JARVIS Run1240 — ToolRegistry deletion-seal regression on latest foundation

## Exact basis

- Repository: `Iam-2squared/ark-ai`.
- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `ec91026bae7ae12b7fad924cc2971c5c8c74f351`.
- Reapplies the test-only deletion-seal regression from Draft PR #420, exact predecessor head `ea0ea2668e861721395f4ec74ffbf08a56c435d6`.
- Predecessor exact-head CI [45300745151](https://github.com/Iam-2squared/ark-ai/actions/runs/45300745151) was GREEN on the older parent; it does not transfer to this rebase.
- New child branch: `research/run1240-tool-registry-delete-seal-rebase`.

## Coverage

- Ordinary deletion of every sealed ToolRegistry slot is rejected.
- Reflective `object.__delattr__` removal of the registration map fails closed at the public bind boundary before any backend call.
- Replacement of the class-level `__delattr__` guard is detected before registry reads or backend access.
- A healthy registry still binds deterministically while keeping the backend disconnected.

All backends are inert test sentinels. No dispatch, permission grant, one-shot authorization or external action is performed. This is local in-process immutability evidence, not tamper-proofing against arbitrary process memory modification or backend attestation.

## Evidence boundary

Test-only. ToolRegistry implementation, registry revision algorithm, ToolCall contract and V1/V2 freezes are unchanged. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required.

No paid/external compute, credentials, hardware, Candidate generation, protected V2 evaluation, UI/frontend work, frozen-contract change, destructive operation or main merge. PR #5/#8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
