# SQLite Durability Findings

Work basis: `28f2fc12e83933a4d5b92c6f7c3b6bfc03b4a640`

These are local prototype findings for the JARVIS foundation branch. They are not repository implementation evidence and do not change any frozen contract or roadmap PASS state.

## Current risk observed in repository code

The current Memory and Action Audit connection helpers execute `PRAGMA journal_mode=WAL` whenever a connection is opened. First-open initialization also inspects schema version before an explicit write lock is acquired. That combination leaves initialization and journal-mode transitions exposed to concurrency races.

Memory expiry cleanup currently selects expired rows before its first write transaction begins. Without an earlier write lock or a revision-bound delete, a stale cleanup reader can race a concurrent refresh.

## Prototype result

A first hardening prototype kept the existing schema-v1 table shape but moved WAL mode switching to bootstrap and acquired `BEGIN IMMEDIATE` before schema inspection. Under 16 simultaneous first-open callers this still produced one `database is locked` failure at round 36 of 40, showing that the journal-mode mutation itself remains a concurrency hazard.

A second prototype stopped mutating persistent journal mode during ordinary/bootstrap opens and used `busy_timeout` plus `BEGIN IMMEDIATE` to serialize schema inspection/creation in the database's existing journal mode.

Local stress results for that prototype:

- concurrent first-open: 16 callers, 40/40 rounds PASS;
- same-revision CAS update: 20 callers, 40/40 rounds PASS with exactly one winner each round;
- concurrent create of the same deterministic identity: 12 callers, 20/20 rounds PASS with exactly one create and 11 domain conflicts each round;
- persisted content-digest tamper: rejected;
- trusted-clock rollback on update: rejected;
- same-version required-index removal: rejected.

## Compatibility constraint discovered

The existing schema-v1 DDL uses `memory_id TEXT PRIMARY KEY`. SQLite reports that column through `PRAGMA table_info` with `notnull=0` on a rowid table. Changing new schema-v1 databases to `TEXT NOT NULL PRIMARY KEY` while validating exact shape would make new and already-created schema-v1 databases disagree.

Therefore a same-version hardening patch should preserve the existing schema-v1 shape during validation. If stronger DDL constraints are required, they should be introduced through an explicit schema version/migration rather than silently changing version 1.

## Recommended repository patch order

1. preserve schema-v1 DDL compatibility;
2. remove journal-mode mutation from ordinary connection creation;
3. serialize first-open schema inspection/creation with an explicit write transaction;
4. validate current-version table/index shape after initialization and reopen;
5. validate persisted Memory rows before surfacing or mutating them;
6. serialize or revision-bind expiry deletion against concurrent refresh;
7. convert expected concurrent create/CAS races into domain-level conflicts;
8. add repeated concurrency tests before integrating Personal Context on top.

No real Candidate work, protected evaluation, external compute, paid service, computer control, or promotion is implied by these findings.
