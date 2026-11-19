# Run1005 — Memory SQLite post-open path recheck

**Work basis:** Draft PR #35 current branch head `5f629d7746bfb2e6ca6124e419ccc43bbb3e1f6f`, containing the Memory reparse-point fence and the first Ruff correction. The parent PR remains Draft/unmerged; this is an isolated follow-up child branch.

## Gap

Memory already preflights its SQLite database and sidecar paths before opening. A pathname can still change between that lstat preflight and SQLite's internal open. The current Memory connections did not recheck the pathname after `sqlite3.connect()` and before setting row factories, issuing PRAGMAs or returning the handle.

## Change

- Recheck the same Memory path after both read/write and read-only SQLite opens.
- On any post-open path admission failure, close the newly opened connection before propagating the original failure.
- Keep explicit bootstrap as the only create-enabled path; ordinary read/write and read-only connections still require an existing database.
- Preserve the Memory v1 schema, CAS/event behavior, expiry semantics and public API.

## Regression coverage

A parameterized synthetic test exercises both connection modes. The SQLite connection wrapper first opens the disposable fixture, then changes the subsequent `Path.lstat()` view to a reparse-point main database. The post-open check must reject before any query or PRAGMA reaches the caller, and the test verifies the connection was closed.

## Limits and safety

A second pathname check narrows the lstat/open race but does not compare the SQLite handle's file identity to the path and is not atomic dirfd custody, authenticated storage or TOCTOU protection. A hostile concurrent replacement can still race between checks. The test uses only synthetic metadata and a disposable local SQLite database; it does not create a Windows junction or claim physical-Windows coverage. No real Memory data, ToolBackend, consent, trusted clock, automatic replay, paid service, external compute, credential, Candidate, V2 evaluation, frozen contract, UI branch or main branch is used.

**Exact-head CI is pending until the Draft child PR is opened; no PASS is claimed. Overall ARK/JARVIS remains NOT_PASSED.**
