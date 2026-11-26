# Run1055 — Memory SQLite Windows reparse-point admission rebase

## Exact work basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent HEAD: `ae6eb0a2ec2fb1db23ac3ae2fccbb03ab24d34b9`.
- Child branch: `research/run1055-memory-sqlite-reparse-rebase`.
- Source: `src/ark/memory/sqlite_store.py`.
- Regression: `tests/test_memory_sqlite_reparse_admission_run1055.py`.

## Gap

The current Memory SQLite path fence rejects POSIX symlinks, hardlinks, non-regular database files and unsafe SQLite sidecars. Windows directory junctions and other reparse points can retain ordinary directory/file mode bits while `stat.S_ISLNK()` is false. The path preflight did not inspect `st_file_attributes`.

## Change

- Pin the portable `FILE_ATTRIBUTE_REPARSE_POINT` bit (`0x400` fallback) and exact local predicate.
- Refuse a rebound predicate or attribute mask before filesystem inspection.
- Reject reparse-point ancestors, the main database file and `-wal` / `-shm` / `-journal` sidecars.
- Preserve Memory v1 DDL, public API, existing alias checks, path budgets and SQLite bootstrap behavior.

## Regression coverage

Five synthetic metadata tests cover an ancestor, main database, sidecar, predicate rebinding and malformed attribute carrier. No privileged Windows junction is created; this is cross-platform synthetic fixture coverage only.

## Limits and safety

These repeated pathname metadata checks are best-effort admission, not atomic descriptor-relative custody, authenticated storage or TOCTOU protection against concurrent owner-controlled replacement. No private database, schema migration, live memory disclosure, physical PC, paid service, external compute, credential, Candidate, protected V2 evaluation, frozen contract, UI branch or main merge is involved.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed. PR #8 remains Draft/unmerged; ARK/JARVIS remains NOT_PASSED.
