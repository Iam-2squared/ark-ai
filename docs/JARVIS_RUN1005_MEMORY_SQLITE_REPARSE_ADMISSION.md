# Run1005 — Memory SQLite reparse-point path admission

**Work basis:** Draft PR #8 exact head `11917b99e177e4601fae5a6f2787ddc548aca91c` (Run1004 checkpoint; its exact-head CI #44613533201 is GREEN 6/6). This work is isolated on `research/memory-sqlite-reparse-admission-run1005`, based on that exact PR #8 head.

## Gap

Memory's local SQLite path fence already uses `Path.lstat()`, rejects POSIX symbolic links, hardlinked/non-regular database files and unsafe `-wal`/`-shm`/`-journal` sidecars. On Windows, a directory junction or another reparse point can retain a directory/file mode while `stat.S_ISLNK()` is false. The Memory path fence did not inspect `st_file_attributes`, so it could admit that path shape.

## Change

- Pin the Windows `FILE_ATTRIBUTE_REPARSE_POINT` bit with a portable `0x400` fallback.
- Add an exact-type, fail-closed reparse-point predicate and pin its local implementation before path inspection.
- Reject reparse-point ancestors, the main Memory SQLite file and each known SQLite sidecar before any SQLite connection is opened.
- Preserve the existing Memory v1 schema, public API, symlink/hardlink checks, path budgets, bootstrap lock and sidecar lifecycle behavior.

## Regression coverage

Five synthetic tests cover:
1. A reparse-point ancestor with ordinary directory mode bits.
2. A reparse-point main database with ordinary regular-file mode bits.
3. A reparse-point SQLite sidecar with ordinary regular-file mode bits.
4. Rebinding the local reparse predicate, refused before filesystem access.
5. Exact integer handling for the platform attribute field, including rejection of a bool carrier.

The tests patch `Path.lstat()` to return synthetic metadata. They do not create a privileged Windows junction or claim physical-Windows coverage.

## Limits and safety

These checks are best-effort local path admission, not atomic dirfd custody, authenticated storage, protection from a concurrent owner-controlled rename, or hash-then-use TOCTOU proof. The change does not alter Memory v1 DDL/public contracts, delete files, repair WAL state, or authorize memory disclosure. No private database, physical PC, paid service, external compute, credential, live observation, ToolBackend, Candidate, V2 evaluation, frozen contract, UI branch or main branch is used.

**Exact-head CI is pending until the Draft child PR is opened; no PASS is claimed. PR #8 remains Draft/unmerged. Overall ARK/JARVIS remains NOT_PASSED.**
