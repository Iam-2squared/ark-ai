# ARK Run1323 — ToolRegistry lookup-hook custody at PermissionGate ingress

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `77d3b2f50d258bb3694afc0d03830e0d44644961`.
- Child branch: `research/run1323-registry-lookup-hook-custody-20261125`.
- This is an isolated follow-up to the existing ToolRegistry / PermissionGate registry-method custody checks. Fresh exact-head CI is required.

## Finding and change

Registered authorization statically pinned the registry's public methods before calling the original unbound `bind` implementation, but did not pin the class-level `__getattribute__` / `__getattr__` lookup hooks. A substituted lookup hook could therefore run when the original method body accessed the registry, before the existing method-identity checks completed.

PermissionGate now captures the import-original static lookup descriptors and checks both class and instance lookup-hook identities through the already-pinned `inspect.getattr_static` before binding or iterating grants. Both the normal object lookup hook and an added fallback hook fail closed without invoking the replacement.

## Regression coverage

Synthetic WRITE authorization replaces each lookup hook with a fail-fast callback. The test requires denial before the callback, grant-generator iteration, one-shot token consumption or backend execution.

## Scope and evidence boundary

Local Python class/instance identity hardening only. No ToolRegistry/PermissionGate public signature, frozen ToolCall contract, capability semantics, durable authorization, audit schema or executor dispatch behavior changes. This is not a Python sandbox or protection against arbitrary same-process code execution; the check protects this reviewed registered-authorization path.

No real backend, live data, external service or trusted clock. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. PR #5/#8 remain Draft/unmerged; PR #9 remains untouched. No paid/external compute, Candidate, protected V2 evaluation, credentials, hardware, destructive operation, UI work, frozen-contract change or main merge.
