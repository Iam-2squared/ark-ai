# ARK Run1337 — Mock completion-audit COMMIT hard-exit regression

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact work-basis HEAD: `2af77814dd01f0959d99a86ddcf9387d94e8053c`.
- Source under test: `src/ark/agency/disconnected_mock_executor.py`.
- Existing adjacent boundaries: Run1288 occurrence-commit hard exit, Run1296 pre-action-audit-commit hard exit, and Run1153 pre-action COMMIT-acknowledgement loss.
- New child branch: `research/run1337-mock-completion-audit-hard-exit-20261125`.

## Gap covered

The prior hard-exit cases stopped after occurrence reservation or after the pre-action audit commit. This case advances the synthetic process-exit boundary through the mock backend call and the second audit commit:

1. The real local PermissionGate method is entered.
2. The pre-action audit event commits.
3. The exact in-process MockToolBackend is called.
4. The completion audit event commits.
5. The child exits before `SQLiteActionAudit.append()` returns and before the caller receives a `MockExecutionReceipt`.

Cold recovery must observe both audit events and the durable occurrence reservation. Reusing the original one-shot with another occurrence ID must fail before the new process-local gate consumes it or the new mock backend runs. A separately created one-shot for the same canonical request remains a distinct authorized mock occurrence.

## Evidence boundary

Synthetic local SQLite files and an exact in-process mock backend only. The test establishes native-COMMIT/process-exit behavior for this specific boundary; it does not establish fsync/power-loss durability, trusted time, independent custody, authenticated consent, cross-store atomicity, receipt reconstruction, or exactly-once external effects. No real backend, live data, external service, paid compute, Candidate, protected V2 evaluation, credentials, hardware, destructive action, frozen-contract change, UI work, or main merge is involved.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No PASS is claimed until that run completes.
