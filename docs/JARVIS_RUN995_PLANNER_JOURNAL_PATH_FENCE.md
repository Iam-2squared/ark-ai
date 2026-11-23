# Run995 — Planner journal path custody

**Work basis:** Draft PR #18 exact head `976aea9d1b5573045ebc18045b3b2ce9d879b9c2`, whose six-job CI run #44538278870 completed GREEN.

**Isolated branch:** `research/planner-journal-path-fence-run995`, proposed as a Draft child of `research/planner-durable-journal-run994`. PR #18 remains Draft/unmerged.

## Change

The durable Planner journal previously passed its pathname directly to `sqlite3.connect`. That left several local path-lifecycle gaps: a symlinked parent or leaf could redirect the database, hardlinks could alias the database, SQLite sidecars could be redirected, and a database removed after initialization could be silently recreated by a later connection.

The journal now applies a repeated no-follow local path preflight:

- Reject lexical `..` traversal, NUL, empty leaf names and oversized native path/sidecar byte lengths.
- Pin relative paths to an absolute lexical pathname without resolving or following symlinks.
- Require every existing ancestor to be a real directory.
- Require an existing database and SQLite sidecars to be single-link regular files.
- Reject orphaned `-wal`, `-shm` or `-journal` files when the main database is absent.
- Recheck the pathname before and immediately after each SQLite open.
- Permit database creation only during the constructor's serialized bootstrap; ordinary create/transition/recovery operations use existing-file-only opens.
- Fail closed with the typed `PlannerJournalPathError`; do not repair, delete, adopt or recreate a missing/aliased database.

No Planner journal table, column, DDL, schema version, event encoding, transition policy, CAS rule or recovery state changed.

## Regression coverage

Eleven named tests (twelve cases including the parameterized non-regular-path test) cover valid relative-path use, missing parents, symlinked ancestors and leaves, post-startup leaf replacement, no-recreation after removal, hardlink aliases, orphaned sidecars, symlinked sidecars, non-regular paths and lexical traversal. Symlink/hardlink cases skip only when the fixture filesystem cannot create the corresponding alias.

All data is synthetic and local. No real tool call, backend dispatch, consent, trusted clock or automatic replay is introduced.

## Limits and safety

These are repeated `lstat` preflights, not atomic directory-descriptor custody. A hostile concurrent owner-controlled rename between the last check and SQLite's internal open remains a TOCTOU boundary; no stronger guarantee is claimed. Parent directories are not auto-created. The change is reversible and does not alter frozen contracts, Memory v1, V2 evaluation, V3 Contract 1, PR #5, main or any UI branch.

## Validation status

Source, tests and this note are saved on the isolated child branch. Exact-head CI will start only after the Draft child PR is opened. No PASS is claimed before all six Windows/Ubuntu × Python 3.11–3.13 jobs complete successfully.


## Run1030 rebase onto current foundations

- Rebased together with the Run994 journal implementation onto Draft PR #8 exact HEAD `b585c61a6e3ca1a9f456175b2a96053a908a500c`.
- Historical PR #19 head `c08c7e9e6c836285362da96663dee903479da98a` passed CI #44549000547 (6/6); that result is not transferred.
- Fresh exact-head CI is required. Repeated lstat checks remain TOCTOU preflights, not atomic dirfd custody.
