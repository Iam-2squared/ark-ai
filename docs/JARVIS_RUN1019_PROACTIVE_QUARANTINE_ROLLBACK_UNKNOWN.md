# ARK AI Run1019 — proactive quarantine rollback before native COMMIT

**Rebase work basis:** Draft PR #8 branch `research/jarvis-foundations`, exact HEAD `e53ffc7db904584a1e817fcfb544012d75eeafc0`. Rebased from PR #93's test-only package; the parent remains OPEN/DRAFT/UNMERGED.

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


## Run1030 rebase onto the current foundation head

- New exact work basis: Draft PR #8 branch `research/jarvis-foundations`, HEAD `b585c61a6e3ca1a9f456175b2a96053a908a500c`.
- Re-applied as a test-only child after the PR #8 checkpoint commit; no production source or frozen contract is changed.
- Previous child PR #97 head `8f521a4f2d059c9d4ada77097086484e69b8bb19` had exact-head CI run #44795817858 GREEN (6/6). That evidence applies only to the previous head and is not transferred to this new rebase.
- Original pre-rebase regression evidence was CI run #44787027172; it is historical evidence only.
- Fresh exact-head six-job CI is required. No local pytest/Ruff PASS is claimed.


## Run1031 rebase onto the latest foundation checkpoint

- Exact work basis: Draft PR #8 branch `research/jarvis-foundations`, HEAD `7d25d985c613a36bf81bf4fa11c0fbaea4928b11` (the Run1030 checkpoint commit).
- Re-applied as a test-only child. Production source, frozen contracts and main are unchanged.
- Previous Run1030 rebase head `2ffc2f34bc08fc09d3be2ae63d5df9a76f13249c` passed exact-head CI #44804482844 (6/6) on its earlier base. That result is historical and is not transferred to this new head.
- Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed.
