# ARK AI Run1033 — proactive quarantine rollback before native COMMIT

## Exact work basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent HEAD at child creation: `c92ef6d65df5e79349e3fa534902117bdfcf263b`.
- This package re-applies PR #119's test-only regression to the latest parent checkpoint. It changes no production source, frozen contract, main branch, or UI file.

## Regression

The disconnected schedule quarantine ledger records only synthetic overdue classifications. A failed explicit SQLite COMMIT must not return a receipt or leave a quarantine row. This package injects `sqlite3.OperationalError` immediately before native COMMIT and verifies:

- exactly one explicit COMMIT attempt and a rollback;
- no native COMMIT;
- cold readback equal to the retained genesis witness;
- zero persisted quarantine rows; and
- SQLite `PRAGMA quick_check` returns `ok`.

The test does not retry, advance a scheduler cursor, notify, dispatch, or authorize an external effect. It complements the separate commit-success/lost-acknowledgement and competing-process uniqueness coverage.

## Prior evidence and current validation

The prior-base PR #119 test head `3f99966c958a1cc30e8a622cdad6f4eede4bc41c` passed exact-head CI run #44823113371 (6/6) on parent `7e7d737195229154775d06baa5b1d8e5c230882b`. That result is historical and does not transfer to this rebase. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed.

## Limits

Synthetic policy, occurrence, timestamp and disposable local SQLite only. This is not trusted time, consent, independent custody, authenticated provenance, power-loss/fsync durability, cross-store atomicity, or exactly-once external effects. Quarantine remains an overdue classification only. No live schedule, OS timer, notification, ToolBackend, paid service, external compute, credentials, Candidate, protected V2 evaluation, frozen contract, UI, PR #5, PR #9, or main branch is changed.
