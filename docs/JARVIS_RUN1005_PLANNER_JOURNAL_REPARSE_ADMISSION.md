# Run1005 — Planner journal SQLite reparse-point path admission

**Work basis:** Draft PR #19 exact head `c08c7e9e6c836285362da96663dee903479da98a`; exact-head CI #44549000547 is GREEN 6/6 (Ubuntu/Windows × Python 3.11–3.13). This isolated child branch is based on that exact PR #19 head.

## Gap

Planner journal path admission already rejects lexical traversal, POSIX symlinks, hardlinked/non-regular database files, orphaned or aliased SQLite sidecars, and missing-database recreation. It did not inspect Windows `st_file_attributes`. A directory junction or another reparse point can report ordinary directory/file mode bits while `stat.S_ISLNK()` is false.

## Change

- Pin the Windows `FILE_ATTRIBUTE_REPARSE_POINT` bit with a portable `0x400` fallback.
- Add an exact-type, fail-closed reparse-point predicate and pin its local implementation before path inspection.
- Reject reparse-point ancestors, the main Planner journal database and known SQLite sidecars before any SQLite connection is opened.
- Preserve the append-only Planner journal DDL, event encoding, transition/CAS rules, recovery behavior and no-automatic-replay boundary.

## Regression coverage

Six synthetic tests cover:
1. A reparse-point ancestor with ordinary directory mode bits.
2. A reparse-point main database with ordinary regular-file mode bits.
3. A reparse-point SQLite sidecar with ordinary regular-file mode bits.
4. Rebinding the local reparse predicate, refused before filesystem access.
5. Exact integer handling for the platform attribute field, including rejection of a bool carrier.
6. A valid unmarked journal path still creates and recovers a synthetic pending plan.

The tests patch `Path.lstat()` to return synthetic metadata. They do not create a privileged Windows junction or claim physical-Windows coverage.

## Limits and safety

These checks are best-effort local path admission, not atomic dirfd custody, authenticated storage, protection from a concurrent owner-controlled rename, or proof against pathname TOCTOU. The change does not alter journal DDL/schema version, append semantics, terminal propagation, commit-unknown handling or recovery quarantine. No real ToolBackend dispatch, consent, trusted clock, automatic replay, Candidate, paid service, external compute, credential, protected V2 evaluation, frozen contract, UI branch or main branch is used.

**Exact-head CI is pending until the Draft child PR is opened; no PASS is claimed. PR #19 remains Draft/unmerged. Overall ARK/JARVIS remains NOT_PASSED.**
