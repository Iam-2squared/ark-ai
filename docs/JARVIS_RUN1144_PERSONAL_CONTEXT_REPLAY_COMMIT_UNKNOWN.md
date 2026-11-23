# Run1144 — Personal Context replay reservation COMMIT ambiguity

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Work-basis HEAD: `e7b49bfb257b0adaf07b3e7b2e52e7f4ca2bf6e8`.
- Child branch: `research/run1144-personal-context-replay-commit-unknown`.
- Test: `tests/test_personal_context_replay_commit_unknown_run1144.py`.

## Finding and change

The existing Personal Context replay suite covers process exit after native COMMIT, but the current exact-head test inventory has no paired COMMIT-acknowledgement-loss case for both possible local SQLite outcomes. This test injects a single COMMIT boundary into the disconnected replay ledger and exercises:

1. A transaction rolled back before the acknowledgement error.
2. A transaction committed natively before the acknowledgement error.

In both cases `reserve()` returns no receipt, attempts COMMIT once, and does not retry. A fresh ledger instance reads the actual persisted outcome. If the row committed, the old witness is stale and the same request is rejected as a duplicate. If the transaction rolled back, the cold witness remains at genesis with no row. Only hash identifiers are stored; synthetic context text is not persisted.

No production Personal Context code, schema/DDL, request identity, retention, revocation, consent, or disclosure policy changes.

## Evidence boundary

Synthetic fixtures and disposable local SQLite only. This does not prove fsync/power-loss durability, independent storage custody, trusted time, consent, revocation freshness, disclosure authority, cross-store atomicity, or exactly-once external effects. A local COMMIT error is resolved by cold readback; it is not permission for automatic replay.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff result is claimed. No paid/external compute, Candidate generation/promotion, protected V2 evaluation, credentials, hardware, UI/frontend work, frozen-contract change, destructive action, or main merge is included. PR #8 and PR #5 remain Draft/unmerged; PR #9 remains untouched; ARK/JARVIS remains NOT_PASSED.
