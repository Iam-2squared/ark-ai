# Run1098 — Personal Context revocation witness root custody

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`
- Work-basis HEAD: `4a000356411254ecad8c436d4b7d594f2833448c`
- Child branch: `research/run1106-context-revocation-witness-root-rebase`
- Source: `src/ark/personal_context_revocation_continuity_review.py`
- Tests: `tests/test_personal_context_revocation_witness_root_custody_run1098.py`

## Change

The retained revocation witness validator now captures the import-original guard-vector root in a function default and requires the module-level root to remain that exact object. This prevents coordinated rebinding of the field/hook vectors and their comparison tuple to equal-valued clones.

Four synthetic tests cover an empty root, equal-valued root replacement, coordinated replacement of all vector roots, and the original default reference. The guard runs before the ledger path or private SQLite is accessed.

## Scope and limits

This is an in-process definition-integrity guard only. A local hash prefix is not authenticated consent, independent storage, trusted time, secure erasure, or permission to disclose personal data. No Memory v1 schema/API or frozen contract changes; no live private data, paid/external compute, Candidate generation, protected V2 evaluation, UI/frontend work, credentials, hardware action, or main merge.

## Validation

The prior PR #233 exact-head CI run 44982306873 was GREEN on its old parent/head; that result does not transfer. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed.