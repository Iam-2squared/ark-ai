# Run1301 — production PlannerJournal path identity

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `8f3b7c528a63110d9085ac9dfefcacd4c405a9f4`.
- Child branch: `research/run1301-planner-journal-path-identity-20261124`.
- Scope: private local PlannerJournal source-path custody only; no Planner schema, event format, public transition API, or frozen contract change.

## Finding

The production `PlannerJournal` retained only a mutable `_path` string. Its filesystem checks revalidated whichever path was currently stored, but the instance did not pin that path to the source selected at construction. Existing path-retarget coverage was in the separate synthetic `planner_journal_review` adapter, not the production `PlannerJournal` class.

## Change

- Store the constructor-selected path in slot-backed `_path` and `_path_identity` references.
- Reject ordinary assignment/deletion of either path slot.
- Pin the class's path guard, bootstrap/connect, recovery, and transition method identities.
- Recheck the exact path object identity at construction, bootstrap, public plan operations, and immediately before SQLite connection.
- Preserve `__dict__` for existing instance-level fault-injection tests; it cannot shadow the slot-backed path.

## Regression coverage

Synthetic local SQLite only: ordinary assignment/deletion, reflective replacement with a different path, equal-but-distinct string replacement, class-level `__setattr__`/`__delattr__`/`_connect` substitution, dictionary shadowing, and subclass construction. The tests require denial before SQLite open and preserve the original database.

## Evidence limits

This is in-process path-identity hardening, not process isolation or a filesystem security boundary. Python reflection can still mutate multiple internal slots together; SQLite pathname checks retain the documented TOCTOU limitation because the driver does not expose its opened descriptor for an atomic no-follow comparison. No trusted time, external dispatch, automatic replay, fsync/power-loss, or exactly-once external-effect guarantee is claimed.

No paid/external compute, Candidate, protected V2 evaluation, credentials, hardware, destructive operation, UI/frontend work, frozen-contract change, or main merge. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required before integration; no PASS is claimed.
