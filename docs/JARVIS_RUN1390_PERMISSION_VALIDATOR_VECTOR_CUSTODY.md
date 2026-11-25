# Run1390 — PermissionGate Validator Vector Custody

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `9fa835e819cd9e212c2e0a2304d3c37b56293b07`.
- Child branch: `research/run1390-permission-validator-vector-custody-20261125`.

## Finding

Two PermissionGate validators retained inventory tuples only through mutable module-level aliases:

- `_GRANT_VECTOR_EPOCH` for CapabilityGrant fields/hooks and their original descriptors.
- `_SPEC_TOKEN_VECTOR_EPOCH` for ToolSpec and OneShotAuthorization field/method/hook inventories.

Joint replacement of each working inventory, purported original inventory and aggregate epoch with matching empty tuples made the strict-zip comparisons vacuous. The grant path could then reach a hostile grant descriptor; the spec/token path could reach substituted ToolSpec or one-shot token descriptors before denial.

## Correction

Both validators now retain the import-time aggregate epoch in keyword-only defaults and compare the current aggregate and every component alias against that captured tuple. The grant validator also retains its class, constructor/post-init descriptors and original budget object. The spec/token validator retains both exact carrier classes and compares class descriptors against the captured inventory vectors.

## Regression coverage

- Jointly replace all grant working/original vectors and the aggregate epoch; a hostile `CapabilityGrant.capability` descriptor must not run and a WRITE token must remain unspent.
- Jointly replace all ToolSpec/OneShotAuthorization working/original vectors and the aggregate epoch; hostile `ToolSpec.name` and `OneShotAuthorization.token_id` descriptors must not run and the WRITE token must remain unspent.

## Scope and evidence limits

Synthetic local authorization only. ToolCall v1, ToolRegistry identity, PermissionGate public API, grant scope/expiry semantics, process-local one-shot semantics and frozen contracts are unchanged. No backend is executed; no durable approval, trusted time, authenticated consent, external exactly-once effect, notification, hardware, credential, paid/external compute, Candidate generation/promotion, protected V2 evaluation, frozen-contract change, main merge or UI/frontend work occurred.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No PASS is claimed until completion. PR #8 remains Draft/unmerged; this child targets only its research branch.
