# ARK AI Run1020 — Memory expiry purge COMMIT outcome matrix

**Work basis:** Draft PR #8 branch `research/jarvis-foundations`, exact HEAD `ff3e9e50ca861486a667bce243ee6ca62af08e28`. This is a test-only child; PR #8 remains OPEN/DRAFT/UNMERGED.

## Finding

Memory deletion/expiry already has pre-commit carrier-drift rollback, post-COMMIT source-drift denial, and process-exit-after-commit coverage. The new matrix isolates the SQLite connection context-manager COMMIT boundary for a bounded, scope-limited expiry purge.

## Regression

The test injects two outcomes after the same due-row selection and matching `expire` event append:

- **Before native COMMIT:** explicitly roll back and raise. Cold reopen must retain the expired row, its original `create` event, and an independent-scope row.
- **After native COMMIT:** commit and then lose the acknowledgement. Cold reopen must show the expired row absent, exactly one matching `expire` event, and the independent-scope row unchanged.

Both paths verify the global event ID sequence, SQLite `quick_check`, and exactly one attempted COMMIT boundary. The committed path performs a separate explicit no-op purge and verifies that it cannot append a duplicate expiry event.

The test is authored; no local pytest/Ruff PASS is claimed. Exact-head Ubuntu/Windows × Python 3.11–3.13 CI is required.

## Limits

Synthetic identifiers/content and disposable local SQLite only. This is not physical erasure, backup deletion, consent, retention authorization, trusted time, authenticated custody, power-loss/fsync durability, cross-store atomicity, or exactly-once external effects. No production source, frozen schema/API, Candidate, protected evaluation, UI, PR #5, PR #9, or main branch is changed.
