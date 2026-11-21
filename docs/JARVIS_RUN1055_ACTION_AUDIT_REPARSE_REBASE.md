# Run1055 — ActionAudit Windows reparse-point path admission rebase

## Exact work basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent HEAD: `ae6eb0a2ec2fb1db23ac3ae2fccbb03ab24d34b9`.
- Child branch: `research/run1055-action-audit-reparse-rebase`.
- Source: `src/ark/agency/audit.py`.
- Regression: `tests/test_action_audit_reparse_point_ancestry_run1055.py`.
- Diagnostic regression: `tests/test_audit_sidecar_safe_diagnostics_run829.py`.

## Finding and change

The ActionAudit path preflight rejected POSIX symlinks, non-directories, hardlinked database files and unsafe SQLite sidecars, but did not explicitly classify Windows `FILE_ATTRIBUTE_REPARSE_POINT`. The package pins the import-time mask, rejects reparse-point ancestors/database leaves/SQLite sidecars, and inspects the main leaf directly with `lstat` before SQLite access.

A present malformed `st_file_attributes` carrier now fails closed instead of being treated as if the reparse bit were absent. Reparse/symlink sidecar denial uses a fixed path-free diagnostic; ordinary directory/hardlink diagnostics retain their bounded metadata.

## Regression coverage

Synthetic stat fixtures cover reparse-point ancestors before parent creation, database leaves before SQLite open, sidecars before reopen, policy-mask rebinding, malformed boolean/null/string/float metadata and the absent-field platform default. A malformed-ancestor test proves the leaf is not inspected after invalid metadata. No privileged junction is created.

## Evidence and limits

This remains repeated pathname metadata admission, not atomic descriptor-relative custody, authenticated audit history or protection against hostile concurrent filesystem replacement. V1 audit schema/event contract remain unchanged; no action is executed and no trusted-clock/authenticated-history claim is made. No paid service, external compute, Candidate, protected V2 evaluation, frozen contract, UI work or main merge is involved.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed. PR #8 remains Draft/unmerged; ARK/JARVIS remains NOT_PASSED.
