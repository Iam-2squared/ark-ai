# Run1125 — Personal Context replay native-COMMIT process-crash rebase

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent HEAD at branch creation: `3940af27c8dc55ccfccadad8cb5c6b63f1e96577`.
- Source fixture: Draft PR #215, branch `research/run1083-personal-context-replay-rebase`, exact source HEAD `516edc5ad99cf68704f2de62f1c81d80dacac865`.
- New branch: `research/run1125-personal-context-replay-crash-rebase`.

## Regression

A spawned local process commits one synthetic Personal Context replay reservation and exits immediately after native SQLite COMMIT, before `reserve()` can return its receipt. A fresh object reads the resulting hash-only witness and verifies:

- exactly one sequence-1 reservation is durable;
- the genesis witness is stale and cannot authorize another reservation;
- the same request identity is denied as a duplicate;
- SQLite `quick_check` remains `ok`;
- synthetic fixture plaintext is absent from the durable database bytes; and
- independent custody remains explicitly false.

The test exercises the existing disconnected replay ledger and preview/request-binding fixtures. It does not modify production source, schema, replay policy or the frozen Personal Context contract.

## Evidence boundary

- Disposable local SQLite, synthetic digests/text and a spawned child process only.
- This proves process exit after native COMMIT and before local receipt return; it is not power-loss/fsync durability, independent custody, trusted time, authenticated consent, revocation freshness, disclosure permission, or exactly-once external effects.
- No live Personal Context data, notification, ToolBackend, dispatch, automatic replay, credentials, paid/external compute, Candidate generation/promotion, protected V2 evaluation, frozen-contract change, UI/frontend work or main merge.
- PR #8 remains Draft/unmerged; this child is also Draft and requires fresh exact-head Windows/Linux × Python 3.11–3.13 CI before any integration or PASS claim.

## Next

Run fresh exact-head CI, inspect all six jobs, and only then consider this isolated test/evidence package for integration into the still-Draft foundation.
