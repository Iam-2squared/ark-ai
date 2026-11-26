# ARK AI Run1019 — Personal Context replay rollback before native COMMIT

**Work basis:** Draft PR #8 branch `research/jarvis-foundations`, exact HEAD `8ac44aabbc8a65b620aa0ccc74ffa44d711a3c8a`. This is a test-only child; the parent remains OPEN/DRAFT/UNMERGED.

## Finding

Run1018 PR #66 covers the opposite outcome: native SQLite COMMIT succeeds, then its acknowledgement is lost. The complementary rollback-side case had not been isolated for the disconnected Personal Context replay ledger.

## Regression

The new test injects `sqlite3.OperationalError` at the ledger's explicit `commit()` call before invoking native COMMIT. It verifies that the ledger's exception path calls rollback, a cold reopen sees the original genesis witness, the persisted request count remains zero, and SQLite `quick_check` is clean.

The test does not retry or construct a reservation receipt. It does not infer consent, disclosure, revocation freshness, independent custody, trusted time, or Tool dispatch authority. The existing hash-only denial ledger and public contracts are unchanged.

The test is authored; no local pytest PASS is claimed. Exact-head Windows/Linux × Python 3.11–3.13 CI is required.

## Limits

Synthetic identifiers, synthetic fixture text and disposable local SQLite only. This is not power-loss/fsync durability, authenticated writer provenance, independent custody, trusted time, consent, disclosure authorization, cross-store atomicity, or exactly-once external effects. No live personal data, real backend, paid service, external compute, credentials, Candidate, protected V2 evaluation, frozen contract, UI, PR #5, PR #9, or main branch is changed.
