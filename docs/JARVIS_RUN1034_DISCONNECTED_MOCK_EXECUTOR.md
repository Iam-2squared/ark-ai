# Run1034 — disconnected mock executor composition rebase

## Scope and exact work basis

- Repository: `Iam-2squared/ark-ai`
- Parent: Draft PR #8, branch `research/jarvis-foundations`
- Exact parent HEAD at branch creation: `06edb64380ee48162adad176e851df63227c91a9`
- Rebased module: `src/ark/agency/disconnected_mock_executor.py`
- Regression suite: `tests/test_disconnected_mock_executor_run992.py`
- This is a reversible mock-only composition. It does not change `agency/__init__.py`, frozen contracts, production dispatch paths, UI, or main.

## Composition

The executor requires exact local foundation instances:

- immutable `ToolRegistry` and its exact `BoundAction`
- exact `PermissionGate`
- `SQLiteActionAudit`
- optional `SyntheticOccurrenceStore` (required for WRITE)
- exact in-process `MockToolBackend`

A registered backend is rejected unless it is the exact in-process mock. The mock computes a deterministic digest from the canonical request ID and performs no filesystem, network, shell, device, model or arbitrary backend operation. Original foundation method references are pinned and instance-level method shadowing is rejected at the composition boundary.

### READ sequence

1. Bind the call against the immutable registry.
2. Check the exact registered effect and authorize the exact scope through PermissionGate.
3. Commit `mock_pre_action` through Action Audit.
4. Rebind the same action immediately before the mock call.
5. Run the deterministic mock and commit `mock_completed`.

### WRITE sequence

1. Bind the call and confirm the registry marks it WRITE.
2. Consume the local process-only one-shot through PermissionGate.
3. Reserve the token digest and occurrence ID in the disconnected durable occurrence ledger.
4. Commit `mock_pre_action` through Action Audit.
5. Rebind the same action immediately before the mock call.
6. Run the deterministic mock and commit `mock_completed`.

The durable occurrence reservation precedes the audit commit. If audit fails, the mock is not called, but the reservation remains and is not automatically released or retried. If the completion audit fails, the mock has already run; the executor raises and does not retry.

## Run1034 hardening

The original Run992 module pinned the mock backend and foundation methods but did not pin the `MockExecutionReceipt` denial descriptors. A class-level replacement could falsify `dispatch_authorized` or another denial property after a successful mock call. The rebase pins the exact receipt class, constructor, fields, denial properties and lookup hooks, and also pins `MockToolResult` lookup hooks. A regression proves receipt descriptor substitution is rejected before audit or mock invocation.

## Evidence

The original PR #14 head `00fee30e4004a56bb73d7161070c6a31661bc9e3` passed exact-head CI run #44528750916 (6/6) on its earlier parent `326001af654078227641546a8f30c6954fcea4a3`. That is historical evidence only; it does not transfer to this rebase. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed.

## Explicit limitations

- The caller-supplied `now_ms` is synthetic policy input, not trusted time.
- The one-shot token issuer and grants are not authenticated consent.
- Occurrence and audit ledgers are separate SQLite databases; there is no cross-store transaction.
- Local SQLite hashes, IDs and append checks do not prove independent custody or resist a compromised interpreter.
- The mock result is not evidence of a real tool effect.
- This is not a production ActionExecutor, scheduler, startup gate or real ToolBackend integration.
- A failure after a durable reservation is quarantined; no automatic retry or uncertain-WRITE replay is allowed.

## Frozen boundaries

V1/V2, Local UI, Launcher, ToolCall/PlanStep, Memory v1, Observation Envelope v1 and V3 Contract 1 remain unchanged. PR #5 remains gated Draft/unmerged. PR #9 remains paused and untouched. No paid API/service, external compute, Candidate, protected V2 evaluation, credentials, physical hardware, real tool dispatch or main merge is involved.

Overall ARK/JARVIS remains NOT_PASSED.
