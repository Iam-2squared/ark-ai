# Run1372 — durable occurrence path guard self-custody

## Exact basis

- Parent: Draft PR #536, branch `research/run1357-occurrence-stat-custody-rebase-20261125`.
- Exact parent HEAD: `b50a635b5e883b96a2130dedf778b902d81fb282`.
- Child branch: `research/run1372-occurrence-path-guard-self-custody-20261125`.
- Source: `src/ark/agency/durable_occurrence_review.py`.
- Regression: `tests/test_occurrence_path_guard_self_custody_run1372.py`.

## Finding and correction

Run1357 pins the import-original stat module, classifiers, reparse mask and sidecar vector. However, internal calls to `_require_original_occurrence_path_policy` still resolved through the mutable module binding. Replacing that guard with a no-op could bypass the pinned path-policy checks before lstat or during a reentrant path callback.

The source now retains `_ORIGINAL_REQUIRE_OCCURRENCE_PATH_POLICY`, verifies that the mutable binding still names that exact function, and routes all internal checks through the retained alias. A substituted guard fails before filesystem inspection; a reentrant replacement is caught immediately after the lstat callback.

## Regression coverage

- Preinstalled no-op guard replacement is rejected before any `Path.lstat` call.
- Guard replacement from inside an lstat callback is rejected before path traversal continues.

The tests use temporary paths only. They do not reserve a token, invoke PermissionGate, open the private occurrence database, or dispatch an action.

## Scope and evidence limits

Occurrence DDL, token/occurrence identity, expiry, reservation transaction, receipt semantics and bounded sidecar retry behavior are unchanged. This is local path-policy custody, not atomic dirfd ownership, authenticated token issuance, trusted time, cross-store atomicity, or exactly-once external effects.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed. No paid/external compute, Candidate, protected V2 evaluation, credentials, hardware, destructive action, frozen-contract change, main merge, or UI/frontend work occurred. PR #5/#8/#9 remain Draft/unmerged; ARK/JARVIS remains NOT_PASSED.
