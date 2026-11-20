# ARK AI Run1034 — proactive quarantine rollback before native COMMIT

## Exact work basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent HEAD at child creation: `06edb64380ee48162adad176e851df63227c91a9`.
- This package re-applies PR #126's test-only regression to the latest parent checkpoint. It changes no production source, frozen contract, main branch, or UI file.

## Regression

The disconnected schedule quarantine ledger records only synthetic overdue classifications. A failed explicit SQLite COMMIT must not return a receipt or leave a quarantine row. This package injects `sqlite3.OperationalError` immediately before native COMMIT and verifies:

- exactly one explicit COMMIT attempt and a rollback;
- no native COMMIT;
- cold readback equal to the retained genesis witness;
- zero persisted quarantine rows; and
- SQLite `PRAGMA quick_check` returns `ok`.

The test does not retry, advance a scheduler cursor, notify, dispatch, or authorize an external effect. It complements the separate commit-success/lost-acknowledgement and competing-process uniqueness coverage.

## Prior evidence and current validation

The same test package on parent `c92ef6d65df5e79349e3fa534902117bdfcf263b`, child head `a40e12169fe234a232c37730ad3839e5a9740464`, passed exact-head CI run #44831333274 (6/6). That result is historical and does not transfer to this rebase. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed.

## Limits

Synthetic policy, occurrence, timestamp and disposable local SQLite only. This is not trusted time, consent, independent custody, authenticated provenance, power-loss/fsync durability, cross-store atomicity, or exactly-once external effects. Quarantine remains an overdue classification only. No live schedule, OS timer, notification, ToolBackend, paid service, external compute, credentials, Candidate, protected V2 evaluation, frozen contract, UI, PR #5, PR #9, or main branch is changed.
