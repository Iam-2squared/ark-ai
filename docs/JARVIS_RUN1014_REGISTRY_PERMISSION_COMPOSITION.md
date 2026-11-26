# Run1014 — exact registry and permission composition

## Scope

This isolated non-UI package reapplies the exact-instance guards previously validated independently in [PR #47](https://github.com/Iam-2squared/ark-ai/pull/47) (ToolRegistry) and [PR #46](https://github.com/Iam-2squared/ark-ai/pull/46) (PermissionGate) onto the current PR #8 foundation work basis. Those source/test changes are reproduced here as normal file edits; neither child branch is merged or modified.

- ToolRegistry constructor, epoch check, and public read/resolve/bind methods reject subclasses before instance attribute access.
- PermissionGate direct and registry-backed authorization reject subclasses before instance attribute access or grant iteration.
- A synthetic registered WRITE is bound and locally authorized through the exact registry and exact gate.
- Reusing the same one-shot token is denied.
- The registered backend is instrumented to fail if called; authorization never dispatches it.

## Interpretation and limits

The one-shot token remains process-local. This test does not establish restart-safe authorization, trusted time, durable consent, external backend identity, exactly-once effects, or audit-before-action. No real tool, personal data, hardware, model, paid service, external compute, or network side effect is used.

No frozen contract, V1/V2/Local UI/Launcher evidence, UI code, protected V2 evaluation, Candidate artifact, PR #5, PR #9, or main branch is changed. PR #8 remains the Draft/unmerged parent workstream. Exact-head CI is pending after this child PR is opened; no PASS is claimed.
