# ARK AI Run1020 — Memory expiry purge COMMIT outcome matrix

**Rebase work basis:** Draft PR #8 branch `research/jarvis-foundations`, exact HEAD `e53ffc7db904584a1e817fcfb544012d75eeafc0`. Rebased from PR #95's test-only package; PR #8 remains OPEN/DRAFT/UNMERGED.

## Finding

Memory deletion/expiry already has pre-commit carrier-drift rollback, post-COMMIT source-drift denial, and process-exit-after-commit coverage. This package isolates the SQLite connection context-manager COMMIT boundary for a bounded, scope-limited expiry purge.

## Regression

The test injects two outcomes after the same due-row selection and matching `expire` event append:

- **Before native COMMIT:** explicitly roll back and raise. Cold reopen must retain the expired row, its original `create` event, and an independent-scope row.
- **After native COMMIT:** commit and then lose the acknowledgement. Cold reopen must show the expired row absent, exactly one matching `expire` event, and the independent-scope row unchanged.

Both paths verify the global event ID sequence, SQLite `quick_check`, and exactly one attempted COMMIT boundary. The committed path performs a separate explicit no-op purge and verifies that it cannot append a duplicate expiry event.

The original package passed exact-head CI run #44731230494 (6/6) on its earlier base. This rebased head requires its own exact-head CI; no PASS is transferred. No local pytest/Ruff PASS is claimed.

## Limits

Synthetic identifiers/content and disposable local SQLite only. This is not physical erasure, backup deletion, consent, retention authorization, trusted time, authenticated custody, power-loss/fsync durability, cross-store atomicity, or exactly-once external effects. No production source, frozen schema/API, Candidate, protected evaluation, UI, PR #5, PR #9, or main branch is changed.


## Run1030 rebase onto the current foundation head

- New exact work basis: Draft PR #8 branch `research/jarvis-foundations`, HEAD `b585c61a6e3ca1a9f456175b2a96053a908a500c`.
- Re-applied as a test-only child after the PR #8 checkpoint commit; no production source or frozen contract is changed.
- Previous child PR #100 head `1cc66232739b13bed737bc259780b57f0e01d8d2` had exact-head CI run #44796209266 GREEN (6/6). That evidence applies only to the previous head and is not transferred to this new rebase.
- Fresh exact-head six-job CI is required. No local pytest/Ruff PASS is claimed.


## Run1031 rebase onto the latest foundation checkpoint

- Exact work basis: Draft PR #8 branch `research/jarvis-foundations`, HEAD `7d25d985c613a36bf81bf4fa11c0fbaea4928b11` (the Run1030 checkpoint commit).
- Re-applied as a test-only child. Production source, Memory v1 schema/public API, frozen contracts and main are unchanged.
- Previous Run1030 rebase head `a3bab6221cb5df259e061786c8b9acf618e8d5ef` passed exact-head CI #44804875953 (6/6) on its earlier base. That result is historical and is not transferred to this new head.
- Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed.


## Run1032 rebase onto the latest foundation checkpoint

- Exact work basis: Draft PR #8 branch `research/jarvis-foundations`, HEAD `7e7d737195229154775d06baa5b1d8e5c230882b` (the Run1031 checkpoint-result HEAD).
- Re-applied as a test-only child; Memory v1 DDL/public API, frozen contracts and main are unchanged.
- Previous Run1031 child head `231eb3702ee4455562b0d2929ffd5f9dea0bac7b` passed exact-head CI #44814312431 (6/6) on its earlier base. That result is historical and is not transferred to this rebase.
- Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed.


## Run1033 rebase onto the latest foundation checkpoint

- Exact work basis: Draft PR #8 branch `research/jarvis-foundations`, HEAD `c92ef6d65df5e79349e3fa534902117bdfcf263b` (the Run1032 checkpoint-result HEAD).
- Re-applied as a test-only child; no production source or frozen contract is changed.
- Previous Run1032 child head `e303eaf1fe7f872a38c0d408d9c5c979fec681be` passed exact-head CI #44823729950 (6/6) on its earlier base. That result is historical and is not transferred to this rebase.
- Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed.


## Run1036 rebase onto the latest foundation checkpoint

- Exact work basis: Draft PR #8 branch `research/jarvis-foundations`, HEAD `784f93d7a48860e774f6d94648ff4e44297c9569` (after the fresh Planner terminal-COMMIT outcome package was integrated).
- Re-applied as a test-only child; Memory v1 DDL/public API, production source and frozen contracts are unchanged.
- Previous child head `b3d3c3f505be68bc50673eecb95deb374e2f7e1d` had CI #44831468494 GREEN (6/6) on its earlier base. That evidence is historical and is not transferred to this rebase.
- Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed.
