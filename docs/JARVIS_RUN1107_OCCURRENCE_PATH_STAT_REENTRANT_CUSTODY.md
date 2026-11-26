# Run1107 — durable occurrence SQLite path-policy reentrancy

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent HEAD at branch creation: `d6ced745480e9d32b6f915acae866ca652326ac6`.
- Source: `src/ark/agency/durable_occurrence_review.py`.
- Existing transient sidecar coverage: `tests/test_occurrence_transient_sqlite_sidecar_run880.py`.
- Existing child branch: `research/run1107-occurrence-path-stat-reentrant-custody`.

## Finding and change

The disconnected occurrence reservation ledger already rejected common POSIX aliases and bounded the single retry for an already-unlinked regular SQLite sidecar. Its path checker still used live stat predicates after `Path.lstat` and metadata callbacks, and did not inspect Windows reparse-point attributes.

The path checker now pins the import-original stat module/classifiers (including the `S_IFMT` dependency), reparse mask and sidecar suffix vector. It rechecks after successful and missing `lstat` callbacks and after `st_mode`, `st_file_attributes` and `st_nlink` accessors. Windows reparse points are denied on ancestors, the main file and sidecars. The existing single bounded resample of an already-unlinked regular sidecar remains intact.

Occurrence table DDL, token/occurrence identity, expiry, reservation transaction and receipt semantics are unchanged.

## Synthetic regression coverage

The new tests cover pre-access and callback-time stat module/predicate substitution, reparse-mask and sidecar-vector replacement, missing-main handling, reentrant metadata accessors, sidecar recheck substitution, and synthetic Windows reparse metadata for ancestor/main/sidecar paths. Tests use temporary paths and inert marker files; they do not reserve tokens, invoke PermissionGate, open a private occurrence database or dispatch an action.

## Limits and evidence

This is local pathname metadata admission for a disconnected reservation fixture. It is not atomic directory-handle custody, authenticated token issuance, trusted time, independent provenance, cross-store atomicity or exactly-once external effects.

No local pytest/Ruff PASS is claimed. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. Existing transient-sidecar CI evidence on other HEADs does not transfer.

No paid/external compute, paid API/service, Candidate generation/promotion, protected V2 evaluation, frozen-contract change, UI/frontend work, credential/account connection, physical hardware action, destructive operation or main merge is involved.

**ARK/JARVIS remains NOT_PASSED.**
