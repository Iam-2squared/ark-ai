# Run992 — Disconnected mock executor composition

## Scope and basis

- Repository: \`Iam-2squared/ark-ai\`
- Isolated branch: \`research/disconnected-mock-executor-run992\`
- Exact base: Draft PR #8 head \`326001af654078227641546a8f30c6954fcea4a3\`
- New module: \`src/ark/agency/disconnected_mock_executor.py\`
- Regression module: \`tests/test_disconnected_mock_executor_run992.py\`
- This is a reversible composition experiment. It does not change \`agency/__init__.py\`, frozen contracts, existing production dispatch paths, or any UI branch.

## Composition

The executor requires exact local foundation instances:

- \`ToolRegistry\` and its exact \`BoundAction\`
- \`PermissionGate\`
- \`SQLiteActionAudit\`
- optional \`SyntheticOccurrenceStore\` (required for WRITE)
- exact \`MockToolBackend\`

A registered backend is rejected unless it is the exact in-process \`MockToolBackend\`. The mock computes a deterministic digest from the canonical request ID and performs no filesystem, network, shell, device, model or arbitrary backend operation. Original foundation method references are pinned and instance-level method shadowing is rejected at the composition boundary.

### READ sequence

1. Bind the call against the immutable registry.
2. Check the exact registered effect and authorize the exact scope through \`PermissionGate\`.
3. Commit \`mock_pre_action\` through Action Audit.
4. Rebind the same action immediately before the mock call.
5. Run the deterministic mock and commit \`mock_completed\`.

### WRITE sequence

1. Bind the call and confirm the registry marks it WRITE.
2. Consume the local process-only one-shot through \`PermissionGate\`.
3. Reserve the token digest and occurrence ID in the disconnected durable occurrence ledger.
4. Commit \`mock_pre_action\` through Action Audit.
5. Rebind the same action immediately before the mock call.
6. Run the deterministic mock and commit \`mock_completed\`.

The durable occurrence reservation precedes the audit commit. If audit fails, the mock is not called, but the reservation remains and is not automatically released or retried. If the completion audit fails, the mock has already run; the executor raises and does not retry.

## Regression coverage authored

Six synthetic cases cover:

- READ grant + pre-action/completion audit sequence
- WRITE one-shot + durable occurrence + audit sequence
- restart with a fresh PermissionGate cannot reuse a committed token digest
- pre-action audit corruption blocks the mock after the occurrence reservation
- arbitrary non-mock backend rejection before permission spend or dispatch
- instance-shadowed Action Audit method rejection before the mock call

These tests use disposable SQLite files and synthetic values only. Exact-head CI is required before treating them as validated.

## Explicit limitations

- The caller-supplied \`now_ms\` is synthetic policy input, not trusted time.
- The one-shot token issuer and grants are not authenticated consent.
- The occurrence and audit ledgers are separate SQLite databases; there is no cross-store transaction.
- Local SQLite hashes, IDs and append checks do not prove independent custody or resist a compromised interpreter.
- The mock result is not evidence of a real tool effect.
- This is not a production ActionExecutor, scheduler, startup gate or real ToolBackend integration.
- A failure after a durable reservation is quarantined; no automatic retry or uncertain-WRITE replay is allowed.

## Frozen boundaries

V1/V2, Local UI, Launcher, ToolCall/PlanStep, Memory v1, Observation Envelope v1 and V3 Contract 1 remain unchanged. PR #5 remains gated Draft/unmerged. PR #9 remains paused and untouched. No paid API/service, external compute, Candidate, protected V2 evaluation, credentials, physical hardware, real tool dispatch or main merge is involved.

**Overall ARK/JARVIS remains NOT_PASSED.**
