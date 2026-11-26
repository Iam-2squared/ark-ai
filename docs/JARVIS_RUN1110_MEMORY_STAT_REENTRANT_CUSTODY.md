# Run1111 — Rebased Run1110 Memory SQLite reentrant stat-policy custody

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent HEAD: `22a22aa08001990739e6c1607d7b1b1cd7b0d9a6`.
- Source package: Draft PR #260, branch `research/run1106-memory-stat-reentrant-rebase`, exact HEAD `aa98e7f3cfed3b68aab1b0823d6415b59a674b68`.
- New child branch: `research/run1111-memory-stat-reentrant-rebase`.
- Production source: `src/ark/memory/sqlite_store.py`.
- Synthetic regression suite: `tests/test_memory_sqlite_stat_reentrant_custody_run1110.py`.

## Rebase evidence

The new parent is a docs-only checkpoint descendant of the prior base `d08cf2bdbc7cdd3142b4ab3945cacf39d29ca607`; the Memory production source and test inputs are unchanged. The source hardening and synthetic tests from PR #264 were therefore reapplied onto exact PR #8 HEAD `22a22aa08001990739e6c1607d7b1b1cd7b0d9a6` without changing Memory v1 DDL, public API, row/event integrity, or CAS semantics.

## Change

The Memory SQLite path fence captures import-original stat classifiers and rechecks policy after filesystem and metadata callbacks, including missing-leaf handling and Windows reparse metadata access. Classification uses captured predicates. The bounded one-time recheck for an already-unlinked regular SQLite sidecar remains intact.

## Synthetic regression coverage

Tests cover pre-access and callback-time stat module/predicate substitution, missing-leaf callback substitution, and reentrant `st_mode` / `st_file_attributes` accessors. Temporary paths and synthetic metadata only; no private Memory database is opened.

## Limits and evidence

This is local dependency-identity and repeated pathname metadata admission, not atomic directory-handle custody, a sandbox, authenticated storage, independent provenance, or TOCTOU protection. No local pytest/Ruff PASS is claimed. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; earlier CI on another parent/head does not transfer.

No paid/external compute, Candidate, protected V2 evaluation, frozen-contract change, UI/frontend work, credentials, physical hardware, destructive operation, or main merge. PR #8 remains Draft/unmerged. **ARK/JARVIS remains NOT_PASSED.**


Rebased child CI is required on this exact branch head. The predecessor PR #260 exact-head run #7059 / 45010626772 is GREEN on the previous base only and is not transferred.


## Run1111 rebase evidence

The predecessor child PR #264 exact head `3d85bd8d8f718335b74969f1eaee2bb628536473` passed Windows/Linux × Python 3.11–3.13 CI run [45014499205](https://github.com/Iam-2squared/ark-ai/actions/runs/45014499205), 6/6. That result does not transfer to this rebased branch; fresh exact-head CI is required.