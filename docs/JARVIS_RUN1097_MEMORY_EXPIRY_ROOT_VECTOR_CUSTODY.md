# Run1097 — Memory expiry bridge guard-vector root custody

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`
- Work-basis HEAD: `d7de07d4d5d1239d3748b43d590dd102a2547c1c`
- Child branch: `research/run1097-memory-expiry-root-vector-custody`
- Source: `src/ark/memory/coherent_expiry_restart_bridge.py`
- Tests: `tests/test_memory_coherent_expiry_root_vector_custody_run1097.py`

## Change

The coherent Memory expiry restart bridge now captures its import-original field-vector and descriptor-vector references in the protocol guard's default arguments. It rejects rebinding of the mutable module-level root names even when the attacker replaces both the current vector and its former reference with the same empty or equal-valued tuple.

Four synthetic cases cover empty paired roots, equal-valued paired roots, descriptor-vector replacement, and the original default references. The rejection occurs at the first protocol gate, before store/scope/retained-snapshot access.

## Scope and limits

This is an in-process guard-definition integrity check only. It does not authenticate a clock, provide independent historical custody, prove cross-epoch atomicity, or authorize expiry/purge. Memory v1 schema/public API and frozen contracts/evidence remain unchanged. No private user database, paid/external compute, Candidate generation, protected V2 evaluation, UI/frontend work, credentials, hardware action, or main merge is involved.

## Validation

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS or CI GREEN is claimed.