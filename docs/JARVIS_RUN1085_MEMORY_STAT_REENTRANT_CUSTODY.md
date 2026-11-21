# Run1085 — Memory SQLite reentrant stat-policy custody

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent HEAD: `916aae6c6578086fee5e83c77c23375712676c90`.
- Source: `src/ark/memory/sqlite_store.py`.
- Existing pre-access coverage: `tests/test_memory_sqlite_stat_predicate_custody_run1071.py`.
- New child branch: `research/run1085-memory-stat-reentrant`.

## Finding and change

The Memory SQLite path fence already pinned the import-original stat module/predicates before filesystem inspection, but the path walker subsequently read live predicates after `Path.lstat` and metadata callbacks. The reparse helper also trusted a potentially reentrant `st_file_attributes` accessor without a post-access policy check.

This change rechecks policy after metadata callbacks, captures the original directory/symlink/regular-file/diagnostic predicates, and binds the reparse attribute mask to its import-time value. Memory v1 DDL, public API, row/event integrity, and CAS behavior are unchanged.

## Synthetic regression coverage

The new tests carry forward pre-access module/predicate substitution cases and add callback-time predicate/module replacement, missing-leaf handling, and reentrant `st_mode` / `st_file_attributes` accessors. Tests use temporary paths and synthetic metadata only; they do not open a private database.

## Limits and evidence

This is local Python dependency-identity and repeated pathname metadata admission. It is not atomic directory-handle custody, a sandbox, authenticated storage, independent provenance, or TOCTOU protection. No local pytest/Ruff PASS is claimed; fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required.

No paid/external compute, Candidate, protected V2 evaluation, frozen-contract change, UI/frontend work, credentials, physical hardware action, or main merge is involved.

**ARK/JARVIS remains NOT_PASSED.**
