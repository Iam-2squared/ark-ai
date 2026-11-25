# Run1388 — PlannerJournal stat module vector custody

Status: isolated source hardening and synthetic regression for Draft PR #8. No roadmap PASS is claimed.

## Finding

PlannerJournal's path verifier compared the current `stat` module with `_ORIGINAL_STAT` and compared three predicates through mutable module aliases. Replacing both module references and all three original predicate aliases together with one fake object made the equality checks pass. A replacement predicate could then execute during filesystem admission.

## Change

The private stat-policy verifier now retains the import-time module and predicate objects in keyword-only defaults. It checks both module bindings and all predicate aliases against those retained objects before any `lstat` or predicate call. PlannerJournal path semantics and public APIs are unchanged.

## Regression coverage

- Preinstalled joint replacement of `stat`, `_ORIGINAL_STAT` and all three predicate aliases must be rejected before `Path.lstat`.
- The same joint replacement installed reentrantly from `Path.lstat` must be rejected before any substituted predicate executes.

Only a synthetic marker file in a temporary directory is used; no SQLite connection or journal mutation occurs.

## Evidence limits

This is local in-process path-policy hardening, not atomic dirfd custody, protection against concurrent filesystem rename, process isolation, or an authenticated filesystem identity. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required.

No live data, ToolBackend dispatch, trusted time, credentials, hardware, paid/external compute, Candidate generation/promotion, protected V2 evaluation, frozen-contract change, main merge or UI/frontend work occurred. PR #8 remains Draft/unmerged.
