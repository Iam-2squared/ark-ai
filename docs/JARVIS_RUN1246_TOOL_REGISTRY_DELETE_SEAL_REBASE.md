# JARVIS Run1246 — ToolRegistry deletion-seal regression rebased

## Exact basis

- Repository: `Iam-2squared/ark-ai`.
- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `609a3cdaf7ad3b08ef90f2398378d9984bdc329d`.
- Rebased test-only package from Draft PR #423, source child HEAD `935bc8d85fd826bd138c1b4ec17c8f14b9a664e2`.
- Test body carried forward unchanged; no ToolRegistry source, registry identity algorithm, ToolCall contract or PermissionGate contract changes.
- Previous child CI [45309506362](https://github.com/Iam-2squared/ark-ai/actions/runs/45309506362) was GREEN 6/6 on the older parent only; it does not certify this rebased head. Fresh exact-head CI is required.

## Coverage

- Ordinary deletion of every sealed ToolRegistry slot is rejected.
- Reflective `object.__delattr__` removal of the registration map fails closed at the public bind boundary before any backend call.
- Replacement of the class-level `__delattr__` guard is detected before registry reads or backend access.
- A healthy registry still binds deterministically while keeping the backend disconnected.

All backends are inert test sentinels. No dispatch, permission grant, one-shot authorization or external action is performed. This is local in-process immutability evidence, not tamper-proofing against arbitrary process memory modification or backend attestation.

## Evidence boundary

Test-only. Frozen contracts and V1/V2/Local UI/Launcher evidence are unchanged. No paid/external compute, credentials, hardware, Candidate generation/promotion, protected V2 evaluation, UI/frontend work, destructive operation, frozen-contract change or main merge. PR #5/#8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no local pytest/Ruff PASS is claimed.
