# Run1107 — ActionAudit reentrant stat-policy custody

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent HEAD at branch creation: `d6ced745480e9d32b6f915acae866ca652326ac6`.
- Source: `src/ark/agency/audit.py`.
- Existing pre-access coverage: `tests/test_action_audit_stat_predicate_custody_run1072.py`.
- Existing reparse-point coverage: `tests/test_action_audit_reparse_point_ancestry_run1055.py`.
- Child branch: `research/run1107-action-audit-stat-reentrant-custody`.

## Finding and change

The ActionAudit path fence pinned the import-original stat module and predicates before filesystem inspection, but it used live predicates after `Path.lstat` and metadata callbacks. The reparse helper also read `st_file_attributes` and `st_mode` without a policy recheck between those accesses. Main-file and SQLite sidecar `st_nlink` callbacks were likewise not followed by a policy check.

The path admission code now:

- captures the import-original directory, regular-file and diagnostic predicates;
- rechecks stat module/predicate identity after successful and missing-leaf `lstat` callbacks;
- rechecks after `st_mode`, `st_file_attributes` and `st_nlink` accessors;
- classifies with captured original predicates and the original reparse mask;
- preserves the single bounded sidecar recheck for an already-unlinked regular inode.

ActionAudit v1 DDL, public APIs, event identity/sequence rules, clock semantics and append behavior are unchanged. No new action or dispatch authority is introduced.

## Synthetic regression coverage

The new test module covers callback-time replacement of each stat predicate and the stat module, missing-leaf callback substitution, reentrant mode/reparse/link-count metadata accessors, and policy replacement during the sidecar recheck. Tests use temporary paths, synthetic metadata and inert file markers only; they do not open a private audit database or perform external actions.

## Limits and evidence

This is local Python dependency-identity and repeated pathname metadata admission. It is not atomic directory-handle custody, a sandbox, authenticated audit history, independent provenance, trusted time, or TOCTOU protection.

No local pytest/Ruff PASS is claimed. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required after this Draft PR is opened. CI results from other branches or parent HEADs do not transfer.

No paid/external compute, paid API/service, Candidate generation/promotion, protected V2 evaluation, frozen-contract change, UI/frontend work, credential/account connection, physical hardware action, destructive operation or main merge is involved.

**ARK/JARVIS remains NOT_PASSED.**
