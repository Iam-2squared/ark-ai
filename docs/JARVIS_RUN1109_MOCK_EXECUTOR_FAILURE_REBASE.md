# Run1109 — disconnected mock executor failure-boundary rebase

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent HEAD: `62047e185d4f8b8fef9a94b3f6441ff1b42c307d`.
- Reapplied from Draft PR #247 exact child HEAD: `1f5c461185f8f5729a581cbe06a6ceae4b0ef528`.
- New child branch: `research/run1109-mock-executor-failure-rebase`.
- Existing composition: `src/ark/agency/disconnected_mock_executor.py`.
- Synthetic regression suite: `tests/test_disconnected_mock_executor_failure_boundaries_run1109.py`.

## Added failure-boundary evidence

1. If the mock backend runs but the completion-audit clock callback fails, the executor reports an ambiguous post-mock audit failure. Backend call count remains one, the pre-action event remains, and no completion event or retry is claimed.
2. A WRITE registration without a durable occurrence store is rejected before one-shot permission consumption, audit append or mock execution.
3. A previously reserved token/occurrence is rejected by durable reservation before the process-local PermissionGate consumes the token, audit append or mock execution.

The package is test-only; executor source, frozen contracts, audit schema, occurrence schema and PermissionGate behavior are unchanged.

## Limits and evidence

Exact in-process `MockToolBackend` only. No network, shell, device, model or arbitrary backend is invoked. Synthetic clocks and local SQLite fixtures do not prove trusted time, cross-store atomicity, authenticated consent, independent custody, exactly-once external effects or real dispatch. The completion-audit failure remains ambiguous and is not retried.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; earlier CI on another parent/head does not transfer. No local pytest/Ruff PASS is claimed.

No paid/external compute, Candidate, protected V2 evaluation, frozen-contract change, credentials, physical hardware, UI/frontend work, destructive operation or main merge. PR #8 remains Draft/unmerged. **ARK/JARVIS remains NOT_PASSED.**
