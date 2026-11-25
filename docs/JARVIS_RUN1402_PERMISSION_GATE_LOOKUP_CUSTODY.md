# Run1402 — PermissionGate class lookup-hook custody

## Exact basis

- Parent: Draft PR #8, branch \`research/jarvis-foundations\`.
- Exact parent work-basis HEAD: \`36368ccc4160727c79fb24704a675d589575b414\`.
- Child branch: \`research/run1402-permission-gate-lookup-custody-20261125\`.
- Child HEAD before this evidence document: \`9f5518c2cf41e073173504b6a3e9fea9b90d466e\`.
- Source blob: \`1077bc8cdc67a3f751a73f90b827e72520cad0d0\`.
- Regression-test blob: \`0d4798988fd80db72e684c49ddc28a75e523b0cb\`.

## Finding and correction

The existing PermissionGate class guard pinned slots, assignment/deletion, initialization, authorization methods and the lock factory, but did not pin class-level \`__getattribute__\` / \`__getattr__\` lookup hooks. Those hooks can be added after a gate instance is created and can intercept later reads of \`_token_lock\` or \`_consumed_tokens\`; checking the underlying slots with \`object.__getattribute__\` does not prove ordinary method lookup used the same class contract.

The guard now captures the exact original class, descriptors, lock factory/type, lookup-hook inventory and an explicit absence sentinel in keyword-only defaults. It checks hook presence and identity before the instance epoch reads token/lock state. Explicit \`None\`, a sentinel-valued hook, equal-valued replacement inventories and hostile hooks are rejected.

## Regression coverage

- Added \`__getattribute__\` and \`__getattr__\` hooks are denied before they execute.
- Explicit \`None\` is distinguished from inherited absence.
- A hook set to the exact absence sentinel is still recognized as present and rejected.
- Equal-valued replacement inventory tuples and a replaced absence sentinel are rejected.
- Exact PermissionGate instances continue to pass the original class/instance guards.
- A subclass with a hostile lookup hook is rejected before its hook executes.

## Scope and evidence limits

No ToolBackend is invoked and no authorization token is spent by these tests. Frozen \`ToolCall\` / \`ToolSpec\` contracts and registry identity formats are unchanged. This is in-process class/instance integrity only: it is not a process sandbox, durable authorization store, restart-safe exactly-once protocol, independent trusted clock or external execution authority. The existing consumed-token set remains process-local.

No credentials, real external action, hardware, paid/external compute, Candidate generation/promotion, protected V2 evaluation, frozen-contract change, main write/merge or UI/frontend work occurred. PR #5/#8 remain Draft/unmerged; PR #9 remains untouched. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no PASS is claimed.
