# Run1110 — Memory SQLite reentrant stat-policy custody rebase

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent HEAD: `d08cf2bdbc7cdd3142b4ab3945cacf39d29ca607`.
- Source package: Draft PR #260, branch `research/run1106-memory-stat-reentrant-rebase`, exact HEAD `aa98e7f3cfed3b68aab1b0823d6415b59a674b68`.
- New child branch: `research/run1110-memory-stat-reentrant-rebase`.
- Production source: `src/ark/memory/sqlite_store.py`.
- Synthetic regression suite: `tests/test_memory_sqlite_stat_reentrant_custody_run1110.py`.

## Rebase evidence

The parent comparison from `62047e185d4f8b8fef9a94b3f6441ff1b42c307d` to `d08cf2bdbc7cdd3142b4ab3945cacf39d29ca607` contains only `docs/PROJECT_STATUS.md` changes; the Memory production source was not changed by that parent checkpoint. The source hardening and synthetic tests from PR #260 were therefore reapplied without changing Memory v1 DDL, public API, row/event integrity, or CAS semantics.

## Change

The Memory SQLite path fence captures import-original stat classifiers and rechecks policy after filesystem and metadata callbacks, including missing-leaf handling and Windows reparse metadata access. Classification uses captured predicates. The bounded one-time recheck for an already-unlinked regular SQLite sidecar remains intact.

## Synthetic regression coverage

Tests cover pre-access and callback-time stat module/predicate substitution, missing-leaf callback substitution, and reentrant `st_mode` / `st_file_attributes` accessors. Temporary paths and synthetic metadata only; no private Memory database is opened.

## Limits and evidence

This is local dependency-identity and repeated pathname metadata admission, not atomic directory-handle custody, a sandbox, authenticated storage, independent provenance, or TOCTOU protection. No local pytest/Ruff PASS is claimed. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; earlier CI on another parent/head does not transfer.

No paid/external compute, Candidate, protected V2 evaluation, frozen-contract change, UI/frontend work, credentials, physical hardware, destructive operation, or main merge. PR #8 remains Draft/unmerged. **ARK/JARVIS remains NOT_PASSED.**


Rebased child CI is required on this exact branch head. The predecessor PR #260 exact-head run #7059 / 45010626772 is GREEN on the previous base only and is not transferred.
