# ARK AI Run1019 — proactive quarantine rollback before native COMMIT

**Work basis:** Draft PR #8 branch `research/jarvis-foundations`, exact HEAD `8ac44aabbc8a65b620aa0ccc74ffa44d711a3c8a`. This is a test-only child; the parent remains OPEN/DRAFT/UNMERGED.

## Finding

PR #53 covers a successful native COMMIT whose acknowledgement is lost, plus competing-process uniqueness for one synthetic expired occurrence. Existing schedule triage tests inspect unchanged and advanced histories, but the rollback outcome at the explicit quarantine-ledger `commit()` call was not separately exercised.

## Regression

The new test injects `sqlite3.OperationalError` before native COMMIT and verifies:

- the ledger calls rollback and returns no quarantine receipt;
- cold readback matches the retained genesis witness;
- no quarantine row was persisted;
- SQLite `quick_check` remains clean.

The test does not retry, advance a scheduler cursor, notify, dispatch, or authorize an external effect. It complements PR #53's commit-success/lost-acknowledgement case.

The test is authored; no local pytest PASS is claimed. Exact-head Windows/Linux × Python 3.11–3.13 CI is required.

## Limits

Synthetic policy, occurrence, timestamp and disposable local SQLite only. This is not trusted time, consent, independent custody, authenticated provenance, power-loss/fsync durability, cross-store atomicity, or exactly-once external effects. Quarantine remains an overdue classification only. No live schedule, OS timer, notification, ToolBackend, paid service, external compute, credentials, Candidate, protected V2 evaluation, frozen contract, UI, PR #5, PR #9, or main branch is changed.
