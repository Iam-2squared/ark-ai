# Run1056 — ActionAudit Windows reparse-point admission rebase

## Exact work basis

- Parent branch: `research/jarvis-foundations`.
- Exact parent HEAD: `b973d9e4e5d4ecdd9912a92274622d07ab23748f`.
- Child branch: `research/run1056-action-audit-reparse-rebase`.
- Source: `src/ark/agency/audit.py`.
- Regressions: `tests/test_action_audit_reparse_point_ancestry_run1055.py` and `tests/test_audit_sidecar_safe_diagnostics_run829.py`.

## Finding and change

The ActionAudit path preflight rejected POSIX symlinks, non-directories, hardlinked database files and unsafe SQLite sidecars, but did not explicitly classify Windows `FILE_ATTRIBUTE_REPARSE_POINT`. This rebase pins the import-time mask, rejects malformed metadata and reparse ancestors/database leaves/SQLite sidecars, and uses direct `lstat` leaf admission before SQLite access.

Reparse/symlink sidecar denial uses a fixed path-free diagnostic. Ordinary directory/hardlink diagnostics retain their bounded metadata. V1 ActionAudit schema and event contract remain unchanged.

## Regression coverage

Synthetic stat fixtures cover reparse ancestors before parent creation, database leaves before SQLite open, sidecars before reopen, policy-mask rebinding, malformed boolean/null/string/float metadata and the absent-field platform default. No privileged junction is created.

## Validation and limits

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed. This remains repeated pathname metadata admission, not atomic descriptor-relative custody, authenticated audit history or protection from hostile concurrent replacement. No action, trusted clock, paid service, external compute, Candidate, protected V2 evaluation, frozen contract, UI work or main merge occurred.

PR #8 remains Draft/unmerged. ARK/JARVIS remains NOT_PASSED.
