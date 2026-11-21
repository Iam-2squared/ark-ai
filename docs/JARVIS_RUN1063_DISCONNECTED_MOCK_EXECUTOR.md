# Run1063 — disconnected mock executor composition on Run1062 foundation

## Exact work basis

- Repository: `Iam-2squared/ark-ai`
- Parent: Draft PR #8, `research/jarvis-foundations`
- Exact parent HEAD at branch creation: `87ee86a333fb851ef21b64ce91e9b15d15e231f6`
- Child branch: `research/run1063-disconnected-mock-executor`
- Added module: `src/ark/agency/disconnected_mock_executor.py`
- Regression suite: `tests/test_disconnected_mock_executor_run992.py`
- This is an isolated, reversible mock-only composition. It does not modify production dispatch paths, package exports, frozen contracts, UI, PR #5, PR #9, or main.

## Composition and ordering

The executor accepts only exact local foundation components: ToolRegistry, PermissionGate, SQLiteActionAudit, optional SyntheticOccurrenceStore (mandatory for WRITE), and the exact in-process MockToolBackend.

READ sequence:
1. Bind the call against the immutable registry.
2. Authorize the exact registered effect and scope through PermissionGate.
3. Commit the pre-action audit event.
4. Rebind the same action immediately before the mock call.
5. Run the deterministic mock and commit the completion audit event.

WRITE sequence:
1. Bind and verify the registry's WRITE effect.
2. Consume the process-local one-shot through PermissionGate.
3. Reserve the token digest and occurrence ID in the disconnected durable occurrence ledger.
4. Commit the pre-action audit event.
5. Rebind immediately before the mock call.
6. Run the deterministic mock and commit the completion audit event.

A failed pre-action audit blocks the mock call. A durable reservation is never automatically released or replayed. A completion-audit failure occurs after the mock has run and is not retried.

## Historical evidence and fresh gate

The predecessor PR #133 child HEAD `9ad5931d35d5df33ecc31bf82cca5d1c420ac345` had exact-head CI run `44841327156` GREEN, 6/6, on its older parent `06edb64380ee48162adad176e851df63227c91a9`. That result does not transfer to this rebase. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required before integration into PR #8.

## Explicit limits

The caller-supplied `now_ms` is synthetic, not trusted time. Grants and one-shot issuers are not authenticated consent. The occurrence and audit ledgers are separate SQLite stores, not cross-store atomic. Local hashes and append checks do not prove independent custody. The mock result is not evidence of a real tool effect. Uncertain WRITE outcomes are quarantined; no automatic retry is authorized.

V1/V2, Local UI, Launcher, ToolCall/PlanStep, Memory v1, Observation Envelope v1 and V3 Contract 1 remain unchanged. PR #8 remains Draft/unmerged; PR #5 remains gated Draft/unmerged; PR #9 remains paused and untouched. No paid service, external compute, credential, physical-device action, real ToolBackend dispatch, protected V2 evaluation, Candidate generation/promotion, or main merge is involved.

Overall ARK/JARVIS remains NOT_PASSED.
