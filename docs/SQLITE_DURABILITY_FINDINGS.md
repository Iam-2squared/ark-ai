# SQLite Durability Findings

Work basis: `69aa036a5efcf691ca4462546885131b3e1e829d`

These are local prototype findings for the JARVIS foundation branch. They are not repository implementation evidence and do not change any frozen contract or roadmap PASS state.

## Current risk observed in repository code

The current Memory and Action Audit connection helpers execute `PRAGMA journal_mode=WAL` whenever a connection is opened. First-open initialization also inspects schema version before an explicit write lock is acquired. That combination leaves initialization and journal-mode transitions exposed to concurrency races.

Memory expiry cleanup currently selects expired rows before its first write transaction begins. Without an earlier write lock or a revision-bound delete, a stale cleanup reader can race a concurrent refresh.

Action Audit currently samples its timestamp before acquiring the SQLite write lock. Two writers can therefore obtain times in one order and commit in another, producing event IDs whose timestamps move backwards.

## Bootstrap findings

A first hardening prototype kept the existing schema-v1 table shape but moved WAL mode switching to bootstrap and acquired `BEGIN IMMEDIATE` before schema inspection. Under 16 simultaneous first-open callers this still produced one `database is locked` failure at round 36 of 40, showing that the journal-mode mutation itself remains a concurrency hazard.

A second prototype stopped mutating persistent journal mode during ordinary/bootstrap opens and used `busy_timeout` plus `BEGIN IMMEDIATE` to serialize schema inspection/creation in the database's existing journal mode.

An additional transaction-boundary check found that Python `sqlite3.executescript()` must not be used to perform the schema DDL after acquiring `BEGIN IMMEDIATE`: it can end the intended transaction boundary. The hardened prototype executes each DDL statement individually inside the explicit transaction.

## Memory prototype result

The current hardened Memory prototype preserves the existing schema-v1 DDL and validates the supported-version table/index shape after bootstrap.

Local stress/results:

- concurrent first-open: 24 callers, 30/30 rounds PASS;
- same-revision CAS update: 20 callers, 30/30 rounds PASS with exactly one winner each round;
- earlier same-identity create stress: 12 callers, 20/20 rounds PASS with exactly one create and domain-level conflicts for the remainder;
- persisted content-digest tamper: rejected;
- non-canonical persisted metadata: rejected;
- deterministic owner/namespace/source -> memory ID mismatch: rejected;
- trusted-clock rollback below the stored update timestamp: rejected;
- same-version required-index removal: rejected;
- expiry deletion is performed after write-lock acquisition and is additionally bound to memory identity, scope, revision, and the expiry predicate.

Expected create/CAS contention is normalized to `MemoryConflictError` rather than leaking a raw SQLite uniqueness/lock exception.

## Action Audit prototype result

The hardened Action Audit prototype uses the same serialized bootstrap rules, validates the current schema/index shape, and samples its trusted mutation time only after obtaining `BEGIN IMMEDIATE`.

Local stress/results:

- concurrent first-open: 24 callers, 40/40 rounds PASS;
- concurrent append: 20 callers, 30/30 rounds PASS;
- committed event timestamps remained monotonic with event order in all 30 contention rounds;
- trusted-clock rollback below the last committed event timestamp: rejected;
- persisted argument-digest tamper: rejected;
- same-version required-index removal: rejected.

The important ordering rule is:

`write lock -> validate persisted state -> trusted clock sample -> mutation/event -> commit`

Sampling the clock before the lock can invert timestamp order when a caller waits behind another writer.

## Compatibility constraint discovered

The existing schema-v1 DDL uses `memory_id TEXT PRIMARY KEY`. SQLite reports that column through `PRAGMA table_info` with `notnull=0` on a rowid table. Changing new schema-v1 databases to `TEXT NOT NULL PRIMARY KEY` while validating exact shape would make new and already-created schema-v1 databases disagree.

Therefore a same-version hardening patch must preserve the existing schema-v1 shape during validation. If stronger DDL constraints are required, they must be introduced through an explicit schema version/migration rather than silently changing version 1.

## SQLite storage-class integrity finding

A new direct-schema check confirmed that SQLite type affinity is not a substitute for persisted-row type validation. The current Memory schema accepts REAL values in INTEGER-affinity columns, including `created_at_ms`, `updated_at_ms`, and `revision`; the existing reader then calls `int(...)`, which can silently truncate values such as `1.5 -> 1`. The v1 `memory_id TEXT PRIMARY KEY` shape also permits NULL values on a rowid table, including more than one NULL row.

Same-version hardening must therefore validate exact values after read rather than relying on DDL affinity:

- persisted integer fields use exact non-bool integer values before conversion;
- timestamps are non-negative and `updated_at_ms >= created_at_ms`;
- revision is an exact integer >= 1;
- optional expiry is NULL or an exact non-negative integer;
- persisted `memory_id` is canonical and recomputes from owner/namespace/source;
- content digest is syntactically valid and matches content;
- metadata is both contract-valid and encoded in canonical JSON form.

An isolated validator rejected 13/13 malformed boundary fixtures covering NULL/incorrect identity, REAL/bool numeric fields, timestamp inversion, bad content digest, non-canonical/oversized metadata, blank owner, and malformed expiry. This remains prototype evidence until repository source/tests land.

## Planner journal integrity finding

A normal per-event SHA-256 hash chain detects modification and interior deletion only when recovery knows the expected tail. Deleting the final event and presenting the previous valid hash as the new tail can otherwise appear valid.

The planner recovery prototype therefore keeps an independently persisted anchor updated in the same transaction, containing event count, last event identity, last event digest, and last trusted timestamp. Recovery verifies both the chain and the anchor so tail truncation also fails closed.

## Recommended repository patch order

1. preserve schema-v1 DDL compatibility;
2. remove journal-mode mutation from ordinary connection creation;
3. serialize first-open schema inspection/creation with `BEGIN IMMEDIATE`;
4. use individual DDL statements rather than `executescript()` inside the acquired bootstrap transaction;
5. validate current-version table/index shape after initialization and reopen;
6. validate persisted Memory/Audit rows before surfacing or mutating them;
7. sample trusted mutation clocks after acquiring the write lock and reject rollback;
8. serialize Memory writers and normalize expected create/CAS contention;
9. revision/expiry-bind Memory cleanup and count only actual deletions;
10. anchor append-only recovery journals independently from their event chains;
11. add repeated thread and process concurrency tests before higher-level integration.

No real Candidate work, protected evaluation, external compute, paid service, computer control, or promotion is implied by these findings.
