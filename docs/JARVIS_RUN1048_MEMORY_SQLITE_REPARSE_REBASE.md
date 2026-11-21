# Run1048 — Memory SQLite reparse-point admission rebase

**Work basis:** Draft PR #8 branch `research/jarvis-foundations`, exact parent HEAD `aa6e47284fbba6f45845274531defdeb5a974252` (Run1047 ToolRegistry custody integration). This child is based on that exact parent; fresh exact-head CI is required.

## Gap

The current Memory SQLite path fence rejects POSIX symlinks, hardlinks, non-regular database files and unsafe SQLite sidecars. Windows directory junctions and other reparse points can retain ordinary directory/file mode bits while `stat.S_ISLNK()` is false. The current fence does not inspect `st_file_attributes`.

## Change

- Pin the portable `FILE_ATTRIBUTE_REPARSE_POINT` bit (`0x400` fallback) and the exact local predicate.
- Refuse a rebound predicate or attribute mask before filesystem inspection.
- Reject reparse-point ancestors, the main database file and `-wal` / `-shm` / `-journal` sidecars.
- Preserve Memory v1 DDL, public API, existing alias checks, path budgets and SQLite bootstrap behavior.

## Regression coverage

Five synthetic metadata tests cover an ancestor, main database, sidecar, predicate rebinding and malformed attribute carrier. No privileged Windows junction is created; this is cross-platform synthetic fixture coverage only.

## Limits and safety

These repeated pathname metadata checks are best-effort admission, not atomic descriptor-relative custody, authenticated storage or TOCTOU protection against concurrent owner-controlled replacement. No private database, schema migration, live memory disclosure, physical PC, paid service, external compute, credential, Candidate, protected V2 evaluation, frozen contract, UI branch or main merge is involved.

**Exact-head CI:** pending for this new branch; no PASS is claimed. PR #8 remains Draft/unmerged. Overall ARK/JARVIS remains NOT_PASSED.
