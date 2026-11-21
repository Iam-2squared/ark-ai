# ARK AI Run1034 — proactive quarantine rollback before native COMMIT (checkpoint rebase)

## Exact work basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent HEAD at this child creation: `35b2cbf9560d2ed214173bed9f25c5912ccf6df8` (Run1034 checkpoint-result HEAD).
- This package re-applies PR #126's test-only regression after the Run1034 checkpoint advanced PR #8. It changes no production source, frozen contract, main branch, or UI file.

## Regression

The disconnected schedule quarantine ledger records only synthetic overdue classifications. A failed explicit SQLite COMMIT must not return a receipt or leave a quarantine row. This package injects `sqlite3.OperationalError` immediately before native COMMIT and verifies:

- exactly one explicit COMMIT attempt and a rollback;
- no native COMMIT;
- cold readback equal to the retained genesis witness;
- zero persisted quarantine rows; and
- SQLite `PRAGMA quick_check` returns `ok`.

The test does not retry, advance a scheduler cursor, notify, dispatch, or authorize an external effect. It complements the separate commit-success/lost-acknowledgement and competing-process uniqueness coverage.

## Prior evidence and current validation

The same test package on parent `c92ef6d65df5e79349e3fa534902117bdfcf263b`, child head `a40e12169fe234a232c37730ad3839e5a9740464`, passed exact-head CI run #44831333274 (6/6). A previous rebase onto parent `06edb64380ee48162adad176e851df63227c91a9`, child head `f919b4fa02b0f960f88d6f4bef4c6b168d9cfa6a`, had CI #44839431167 **IN PROGRESS** when the checkpoint advanced; that run is historical for its old base and does not transfer. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required for this checkpoint rebase. No local pytest/Ruff PASS is claimed.

## Limits

Synthetic policy, occurrence, timestamp and disposable local SQLite only. This is not trusted time, consent, independent custody, authenticated provenance, power-loss/fsync durability, cross-store atomicity, or exactly-once external effects. Quarantine remains an overdue classification only. No live schedule, OS timer, notification, ToolBackend, paid service, external compute, credentials, Candidate, protected V2 evaluation, frozen contract, UI, PR #5, PR #9, or main branch is changed.
