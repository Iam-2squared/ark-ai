# Run1098 — Personal Context revocation witness root custody

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`
- Work-basis HEAD: `d7de07d4d5d1239d3748b43d590dd102a2547c1c`
- Child branch: `research/run1098-context-revocation-witness-root-custody`
- Source: `src/ark/personal_context_revocation_continuity_review.py`
- Tests: `tests/test_personal_context_revocation_witness_root_custody_run1098.py`

## Change

The retained revocation witness validator now captures the import-original guard-vector root in a function default and requires the module-level root to remain that exact object. This prevents coordinated rebinding of the field/hook vectors and their comparison tuple to equal-valued clones.

Four synthetic tests cover an empty root, equal-valued root replacement, coordinated replacement of all vector roots, and the original default reference. The guard runs before the ledger path or private SQLite is accessed.

## Scope and limits

This is an in-process definition-integrity guard only. A local hash prefix is not authenticated consent, independent storage, trusted time, secure erasure, or permission to disclose personal data. No Memory v1 schema/API or frozen contract changes; no live private data, paid/external compute, Candidate generation, protected V2 evaluation, UI/frontend work, credentials, hardware action, or main merge.

## Validation

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS or CI GREEN is claimed.