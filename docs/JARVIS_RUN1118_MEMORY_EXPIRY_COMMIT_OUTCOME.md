# ARK AI Run1118 — Memory expiry purge COMMIT outcome matrix

**Exact work basis:** Draft PR #8 branch `research/jarvis-foundations`, commit `a5e961876eb24adba97573bb34228740c1344d9e`.  
**Child branch:** `research/run1118-memory-expiry-commit-outcome-rebase`.  
**Scope:** test-only reapplication of the older PR #100 Run1020 expiry COMMIT-outcome matrix. No production source, Memory v1 DDL, public API or frozen contract is changed.

## Finding and regression

The expiry purge appends its matching `expire` event in the same SQLite write transaction as the row deletion. The test injects two distinct outcomes after identical due-row selection and event append:

- **Before native COMMIT:** roll back and raise. Cold reopen must retain the expired row, its original `create` event, and an independent-scope row.
- **After native COMMIT:** commit and then lose the acknowledgement. Cold reopen must show the expired row absent, exactly one matching `expire` event, and the independent-scope row unchanged.

Both outcomes require exactly one COMMIT attempt, the exact global event-ID sequence and SQLite `quick_check`. The committed case performs a separate explicit no-op purge and proves that it cannot append a duplicate expiry event.

## Evidence boundary

Synthetic identifiers/content and disposable local SQLite only. This is not physical erasure, backup deletion, consent, retention authorization, trusted time, authenticated custody, power-loss/fsync durability, cross-store atomicity or exactly-once external effects. A COMMIT acknowledgement loss is an UNKNOWN outcome to be resolved by readback; this fixture does not authorize an automatic retry.

## Validation

One parameterized test covers rollback-before-COMMIT and commit-success/lost-acknowledgement. It is rebased onto the exact Run1117 parent commit above. **Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no PASS is claimed at authoring time.** Earlier PR #100 CI on a different base does not transfer.

PR #8 remains Draft/unmerged; PR #5 remains gated Draft/unmerged; PR #9 remains untouched and UI remains paused. No paid/external compute, Candidate generation/promotion, protected V2 evaluation, credentials, physical hardware action, destructive operation or main merge is included. **ARK/JARVIS remains NOT_PASSED.**
