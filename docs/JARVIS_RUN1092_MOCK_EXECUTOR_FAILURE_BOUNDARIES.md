# Run1092 — disconnected mock executor failure ordering

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent HEAD: `d7de07d4d5d1239d3748b43d590dd102a2547c1c`.
- Child branch: `research/run1092-mock-executor-failure-boundaries`.
- Existing composition: `src/ark/agency/disconnected_mock_executor.py`.
- New tests: `tests/test_disconnected_mock_executor_failure_boundaries_run1092.py` (3 tests).

## Added failure-boundary evidence

1. If the mock backend has run but the completion-audit clock callback fails, the executor raises the explicit post-mock audit error. The backend call count remains exactly one, the pre-action event remains committed, and no completion event or retry is claimed.
2. A WRITE registration without a durable occurrence store is rejected before one-shot permission consumption, audit append or mock execution.
3. If a token/occurrence was already durably reserved, the PermissionGate consumes the presented one-shot token and the durable occurrence ledger rejects replay before audit or mock execution. No second occurrence or backend call is produced.

These cases extend the existing READ/WRITE composition tests without changing the executor, frozen contracts, audit schema, occurrence schema or PermissionGate behavior.

## Limits

All backends remain the exact in-process `MockToolBackend`; no network, shell, device, model or arbitrary backend is invoked. The synthetic `now_ms` values and local SQLite stores do not prove trusted time, cross-store atomicity, authenticated consent, independent custody, exactly-once external effects or real dispatch. The completion-audit failure is intentionally treated as an ambiguous local outcome; the executor does not retry.

No local pytest/Ruff result is claimed. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required after opening the Draft child PR. PR #8 remains Draft/unmerged; PR #5 remains Draft/unmerged; PR #9 and all UI/frontend work remain paused and untouched. No paid/external compute, Candidate, protected evaluation, credentials, destructive operation or main merge is involved. ARK/JARVIS remains NOT_PASSED.
