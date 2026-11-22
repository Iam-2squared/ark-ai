# Run1107 — proactive SQLite path-policy reentrancy and reparse admission

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent HEAD at branch creation: `d6ced745480e9d32b6f915acae866ca652326ac6`.
- Source: `src/ark/proactive_synthetic_review.py`.
- Existing path coverage: `tests/test_proactive_sqlite_alias_preaccess_run799.py`, `tests/test_proactive_transient_journal_preflight_run801.py`, and `tests/test_proactive_native_path_preflight_run903.py`.
- Child branch: `research/run1107-proactive-path-stat-reentrant-custody`.

## Finding and change

The proactive SQLite path preflight rejected common POSIX aliases and bounded native paths, but it used live stat predicates after `Path.lstat` and metadata callbacks. It also did not reject Windows reparse-point attributes. The sidecar suffix vector and filesystem encoding function were not pinned by the path helper.

The helper now captures import-original `os.fsencode`, stat module/classifier identities, the `S_IFMT` dependency, reparse mask and sidecar suffix tuple. It rechecks policy after successful and missing `lstat` callbacks, path/sidecar construction, and `st_mode`, `st_file_attributes` and `st_nlink` accessors. Classification uses captured predicates. Windows reparse points are denied for ancestors, the main file and SQLite sidecars. The existing one-time resample of an already-unlinked regular sidecar remains bounded.

Proactive SQLite DDL, row format, eligibility/CAS semantics, timestamps, and denial-only notification/dispatch/consent properties are unchanged.

## Synthetic regression coverage

The new tests cover pre-access module/predicate/encoding/mask/sidecar-vector substitution, callback-time predicate/module replacement, missing-main handling, reentrant mode/reparse/link-count accessors, sidecar recheck substitution, and Windows reparse metadata on ancestor/main/sidecar paths. Tests use temporary paths, synthetic metadata and inert marker files; no private proactive database, scheduler service, notification or external effect is exercised.

## Limits and evidence

This is local Python dependency-identity and repeated pathname metadata admission. It is not atomic directory-handle custody, a sandbox, authenticated consent, trusted time, independent provenance or TOCTOU protection. `ELIGIBLE_PREVIEW` remains non-authoritative.

No local pytest/Ruff PASS is claimed. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required.

No paid/external compute, paid API/service, Candidate generation/promotion, protected V2 evaluation, frozen-contract change, UI/frontend work, credential/account connection, physical hardware action, destructive operation or main merge is involved.

**ARK/JARVIS remains NOT_PASSED.**
