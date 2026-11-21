# Run1039 — ActionAudit Windows reparse-point path custody

## Exact work basis

- Parent: Draft PR #8, branch research/jarvis-foundations.
- Exact parent HEAD: 784f93d7a48860e774f6d94648ff4e44297c9569.
- Source: src/ark/agency/audit.py.
- Regression: tests/test_action_audit_reparse_point_ancestry_run1039.py.
- Scope is local audit-database path admission before mkdir or SQLite open.

## Finding

The ActionAudit path preflight rejected POSIX symlinks, non-directories, hardlinked database files and unsafe SQLite sidecars. On Windows, a junction or another reparse-point directory can report directory mode without stat.S_ISLNK being true. The ancestor check therefore did not explicitly reject every redirected path component.

## Change

- Pin the import-time FILE_ATTRIBUTE_REPARSE_POINT mask.
- Recognize both POSIX symlinks and Windows reparse-point attributes.
- Apply the check to every existing ancestor, the database leaf and each SQLite WAL/SHM/rollback-journal sidecar.
- Use lstat-based leaf existence rather than exists()+is_symlink(), so a reparse leaf is classified without following it.
- Preserve the existing exact-path, parent traversal, hardlink, orphan-sidecar and SQLite admission rules.

## Regression coverage

Cross-platform synthetic stat metadata covers reparse-point ancestors before directory creation, reparse-point database leaves before SQLite open, reparse-point sidecars before reopen, and mutation of the pinned reparse policy mask. These tests do not create privileged junctions or perform a database write through a redirected path.

## Limits and frozen boundaries

This remains repeated local filesystem metadata checking, not atomic descriptor-relative traversal, authenticated audit history, protection against a hostile concurrent filesystem writer, or a trusted-clock proof. The v1 audit schema and event contract remain unchanged. No audit event, real action, backend dispatch, V2 evaluation, Candidate, paid service, UI, PR #5, PR #9 or main merge is performed.
