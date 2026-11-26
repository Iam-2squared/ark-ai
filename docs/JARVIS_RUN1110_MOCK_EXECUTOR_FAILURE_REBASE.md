# Run1110 — disconnected mock executor failure-boundary rebase

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent HEAD: `d08cf2bdbc7cdd3142b4ab3945cacf39d29ca607`.
- Reapplied from Draft PR #263 exact child HEAD: `d7ea65def2a8eecd28695f309bb5c86877e2f951`.
- New child branch: `research/run1110-mock-executor-failure-rebase`.
- Existing composition: `src/ark/agency/disconnected_mock_executor.py`.
- Synthetic regression suite: `tests/test_disconnected_mock_executor_failure_boundaries_run1110.py`.

## Added failure-boundary evidence

1. If the mock backend runs but the completion-audit clock callback fails, the executor reports an ambiguous post-mock audit failure. Backend call count remains one, the pre-action event remains, and no completion event or retry is claimed.
2. A WRITE registration without a durable occurrence store is rejected before one-shot permission consumption, audit append or mock execution.
3. A previously reserved token/occurrence is rejected by durable reservation before the process-local PermissionGate consumes the token, audit append or mock execution.

The package is test-only; executor source, frozen contracts, audit schema, occurrence schema and PermissionGate behavior are unchanged.

## Limits and evidence

Exact in-process `MockToolBackend` only. No network, shell, device, model or arbitrary backend is invoked. Synthetic clocks and local SQLite fixtures do not prove trusted time, cross-store atomicity, authenticated consent, independent custody, exactly-once external effects or real dispatch. The completion-audit failure remains ambiguous and is not retried.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; earlier CI on another parent/head does not transfer. No local pytest/Ruff PASS is claimed.

No paid/external compute, Candidate, protected V2 evaluation, frozen-contract change, credentials, physical hardware, UI/frontend work, destructive operation or main merge. PR #8 remains Draft/unmerged. **ARK/JARVIS remains NOT_PASSED.**


Rebased child CI is required on this exact branch head. The predecessor PR #263 exact-head run #7062 / 45010872740 is GREEN on the previous base only and is not transferred.
