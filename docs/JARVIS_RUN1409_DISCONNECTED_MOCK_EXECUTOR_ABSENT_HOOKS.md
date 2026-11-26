# Run1409 — Disconnected mock executor absent-hook custody

Status: isolated source hardening and synthetic regression for Draft PR #8. No roadmap PASS is claimed.

## Finding

The disconnected mock executor retained class-hook vectors for `MockToolBackend`, `MockToolResult` and `MockExecutionReceipt`, but represented absent `__new__`, `__getattribute__` and `__getattr__` entries with `dict.get()`'s implicit `None`. An explicit `None` installed in a class namespace therefore compared equal to absence. Installing the sentinel value itself would also be ambiguous if the check relied only on a defaulted lookup.

## Change

- Capture one unique absent-class-hook sentinel and use it when building the three hook vectors.
- Retain the sentinel and the three exact component type objects in the import-time validator epoch.
- Check namespace membership separately for entries expected to be absent; for present entries, require exact descriptor identity.
- Keep the existing backend/result/receipt field checks and the executor's pre-dispatch component checks unchanged.
- Reject a replaced sentinel or replaced type/vector epoch before component validation, registry binding, audit append or mock execution.

## Regression coverage

- For each of the three exact component classes, explicit `None` is rejected for each of the three absent hooks.
- Installing the exact absence sentinel as a class hook is also rejected.
- All `__new__` allocation-slot probes run in isolated subprocesses; lookup-hook probes restore the class namespace before checking audit state.
- Replacing the module's sentinel binding is rejected by the retained validator epoch.
- Every rejection leaves the mock backend call count at zero and the ActionAudit event list empty.

## Scope and evidence limits

Synthetic in-process fixtures only. No schema, DDL, public API, ToolCall, PermissionGate, ActionAudit, occurrence-ledger or frozen contract changed. The executor still accepts only the exact deterministic in-process `MockToolBackend`; no real backend, network, shell, device, model, notification or external service is connected.

This is class-namespace integrity within one Python process, not a Python sandbox, independent custody, trusted-clock proof, authenticated consent, cross-store atomicity, fsync/power-loss durability or exactly-once external-effect evidence.

No paid/external compute, paid API/service, Candidate generation/promotion, protected V2 evaluation, credentials, new account connection, hardware action, destructive operation, main write/merge or UI/frontend work occurred. PR #5/#8/#9 remain Draft/unmerged; UI/frontend development remains paused.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff result or PASS is claimed.
