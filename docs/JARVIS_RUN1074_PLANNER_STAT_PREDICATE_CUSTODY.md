# Run1074 — Planner journal stat-predicate custody

## Exact work basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Parent HEAD: `2e408656ae0661626e6bc3fb234006819ef2ccfc`.
- Child branch: `research/run1074-planner-stat-predicate-custody`.
- Production source: `src/ark/agency/planner_journal_review.py`.
- Regression: `tests/test_planner_journal_stat_predicate_custody_run1074.py`.

## Change

The disconnected, replay-only Planner journal now pins the import-original `stat` module and the exact `S_ISDIR`, `S_ISLNK`, and `S_ISREG` predicates used for ancestor, database-leaf and SQLite-sidecar path admission. The existing reparse-policy guard rejects a replaced module or predicate before `lstat`, directory creation or SQLite access.

The Windows reparse attribute policy, path rules, journal schema, hash chain, Planner transitions and recovery semantics are unchanged. Recovered RUNNING steps remain UNKNOWN; this package adds no dispatch or replay authority.

## Regression coverage

Four synthetic substitutions (three predicates and the module binding) require the existing fail-closed diagnostic before any `Path.lstat`. No privileged junction, journal database, live plan or external effect is used.

## Limits and validation

This is local in-process dependency-identity hardening, not a Python sandbox, atomic directory-handle custody, hostile-writer protection, trusted time, independent provenance, power-loss durability or exactly-once external effects. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no local pytest/Ruff PASS is claimed.

No paid service, external compute, Candidate, protected V2 evaluation, frozen contract, UI work, credentials, physical hardware or main merge is involved.

**ARK/JARVIS remains NOT_PASSED.**
