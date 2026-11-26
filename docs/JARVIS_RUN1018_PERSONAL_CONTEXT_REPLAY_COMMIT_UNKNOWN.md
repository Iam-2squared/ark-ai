# ARK AI Run1018 — Personal Context replay COMMIT-UNKNOWN

**Work basis:** Draft PR #8 branch `research/jarvis-foundations`, exact HEAD `40c3467d6e45c477780f1c83b2a1cfa53111f932`. This is a test-only child; the parent remains OPEN/DRAFT/UNMERGED.

## Finding

The disconnected Personal Context replay ledger commits a hash-only reservation before constructing its receipt. Existing tests cover duplicate requests, stale witnesses, process races, and post-COMMIT receipt-constructor substitution. They did not explicitly simulate a native SQLite COMMIT that succeeds while the caller loses its acknowledgement.

## Regression

The new test wraps only the target disposable SQLite connection. Its COMMIT delegates to the native connection and then raises a synthetic `sqlite3.OperationalError`. It requires:

- the caller receives no reservation receipt;
- rollback after the lost acknowledgement does not erase the already committed row;
- cold reopen observes exactly one contiguous hash-only row and a clean SQLite `quick_check`;
- the pre-COMMIT witness is stale and cannot append a different request;
- even a fresh local witness cannot reserve the same request ID again;
- synthetic fixture text is absent from the persisted rows.

The test is authored; no local pytest PASS is claimed. Exact-head Windows/Linux × Python 3.11–3.13 CI is required.

## Limits

This is disposable local SQLite evidence, not power-loss/fsync durability, authenticated writer provenance, independent custody, trusted time, consent, revocation freshness, disclosure permission, cross-store atomicity, or exactly-once external effects. The ledger remains denial-only and disconnected. No live personal data, model, ToolBackend, sensor, network action, paid service, external compute, credential, Candidate, protected V2 evaluation, frozen contract, UI, PR #5, PR #9, or main branch is changed.
