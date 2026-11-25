# Run1374 — ActionAudit reparse-policy guard self-custody

## Exact basis

- Parent: Draft PR #538, branch `research/run1359-action-audit-stat-custody-rebase-20261125`.
- Exact parent HEAD: `0fb15ea05f04892dc7e10296ea8472bb5719b242`.
- Child branch: `research/run1374-action-audit-guard-self-custody-20261125`.
- Source: `src/ark/agency/audit.py`.
- Regression: `tests/test_action_audit_reparse_guard_self_custody_run1374.py`.

## Finding and correction

Run1359 pins the import-original stat module/classifiers and reparse-point mask, then rechecks them around filesystem callbacks. However, internal checks still resolved `_require_original_reparse_policy` through its mutable module binding. A replacement no-op could bypass those checks before lstat or after a reentrant lstat callback.

The source now retains `_ORIGINAL_REQUIRE_REPARSE_POLICY`, verifies that the mutable public binding still names that exact function, and routes internal checks through the retained alias.

## Regression coverage

- A preinstalled no-op guard replacement is rejected before any `Path.lstat` call.
- A guard replacement from inside an lstat callback is rejected immediately after that callback, before path traversal continues.

Temporary paths only; no ActionAudit database is opened and no event is appended.

## Scope and evidence limits

ActionAudit v1 DDL, public event fields, schema/version, append semantics, timestamp policy and audit-before-action ordering are unchanged. These are local pathname-policy checks, not atomic dirfd custody, trusted time, authenticated audit history, or permission to dispatch.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed. No paid/external compute, Candidate, protected V2 evaluation, credentials, hardware, destructive action, frozen-contract change, main merge, or UI/frontend work occurred. PR #5/#8/#9 and parent PR #538 remain Draft/unmerged; ARK/JARVIS remains NOT_PASSED.
