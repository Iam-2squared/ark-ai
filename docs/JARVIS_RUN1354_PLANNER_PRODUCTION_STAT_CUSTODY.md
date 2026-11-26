# ARK Run1354 — Production PlannerJournal stat-policy custody

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `8c969bbd2dc83c800b7bad998fd8e480aec941e7`.
- Child branch: `research/run1354-planner-production-stat-custody-20261125`.
- Implementation and regression head before this evidence note: `f55ef2c91ba672761bbc2747783ed01f02cdc41a`.
- Production file: `src/ark/agency/planner_journal.py`.
- Regression module: `tests/test_planner_journal_production_stat_custody_run1354.py`.

## Finding and correction

The production PlannerJournal path preflight used the live `stat.S_ISDIR`, `stat.S_ISLNK` and `stat.S_ISREG` module bindings while classifying ancestors, the database leaf and SQLite sidecars. The existing production path-identity guard did not pin those classifier identities. A substituted predicate could therefore misclassify an `lstat` result; a reentrant `lstat` callback could replace the classifier between preflight and use.

The path guard now retains the import-time stat module and exact predicates, rejects replacement before filesystem inspection, classifies through the retained callables, and rechecks policy after each metadata callback and missing-path branch. The sidecar order remains fail-closed: orphaned sidecars are rejected before their metadata is classified.

## Regression coverage

- Preinstalled replacement of each of the three stat predicates is rejected before `Path.lstat`.
- Rebinding the stat module is rejected before `Path.lstat`.
- Predicate/module replacement during ancestor `lstat` is rejected before classification.
- Replacement during missing database and missing sidecar callbacks is rejected.
- A valid regular existing path remains admissible.

## Scope and evidence boundary

No Planner journal schema/DDL, hash chain, transition policy, CAS semantics, receipt shape, recovery behavior or public API changed. This is import-time in-process classifier identity hardening around the existing repeated pathname preflight; it is not atomic directory-descriptor custody, a sandbox, protection against hostile concurrent rename, fsync/power-loss certification, trusted time, authorization, automatic replay or exactly-once external-effect evidence. RUNNING recovery remains ambiguous and dispatch remains unauthorized.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS or CI PASS is claimed. Synthetic temporary paths only; no real ToolBackend, live personal data, paid/external compute, Candidate, protected V2 evaluation, credentials, hardware, destructive operation, frozen-contract change, main merge or UI work occurred. PR #5 and PR #8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
