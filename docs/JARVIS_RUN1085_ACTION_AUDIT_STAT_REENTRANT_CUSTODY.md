# Run1085 — ActionAudit reentrant stat-policy custody

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent HEAD: `916aae6c6578086fee5e83c77c23375712676c90`.
- Source: `src/ark/agency/audit.py`.
- Existing pre-access coverage: `tests/test_action_audit_stat_predicate_custody_run1072.py`.
- New child branch: `research/run1085-action-audit-stat-reentrant`.

## Finding and change

The existing ActionAudit path fence pinned the import-original stat module and predicates before path inspection, but subsequent `Path.lstat` and metadata access could rebind the module/predicates before the live attributes were used. This change rechecks the original policy after metadata callbacks, captures the original directory/regular-file classifiers, and uses the captured symlink predicate and reparse mask in `_is_reparse_point`. It also preserves the bounded sidecar diagnostic through the captured `S_IFMT` predicate.

The ActionAudit v1 schema, event identity, append ordering, and audit semantics are unchanged. No action execution or authorization is added.

## Synthetic regression coverage

The new test module carries forward pre-access stat/module substitution checks and adds callback-time predicate/module substitution, missing-leaf handling, and reentrant `st_mode` / `st_file_attributes` accessors. Tests use temporary paths and synthetic metadata only.

## Limits and evidence

This is local Python dependency-identity and repeated pathname metadata admission. It is not atomic directory-handle custody, a sandbox, independently authenticated audit history, a trusted clock, consent, or proof of external effects. No local pytest/Ruff PASS is claimed; fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required.

No paid/external compute, Candidate, protected V2 evaluation, frozen-contract change, UI/frontend work, credentials, physical hardware action, or main merge is involved.

**ARK/JARVIS remains NOT_PASSED.**
