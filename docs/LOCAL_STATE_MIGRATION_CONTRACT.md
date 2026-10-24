# ARK Local State Migration Contract

Status: foundation contract for reversible local-first state evolution. This document does not authorize a roadmap PASS, external compute, Candidate generation, protected evaluation opening, or main merge.

## Scope

This contract governs schema evolution for ARK-owned local persistent stores such as Memory, Action Audit, durable authorization, planner recovery, proactive state, and controlled self-improvement ledgers.

It applies only to ARK-owned state. Frozen V1/V2/Local UI/Launcher evidence and the frozen V3 Contract are not migration targets.

## Core invariants

1. **Explicit versioning.** Every persistent store has an integer schema version. A supported current version must also pass exact required table/index/constraint validation.
2. **No silent downgrade.** If a database advertises a version newer than the running code supports, startup fails closed for that component. The database must not be rewritten.
3. **No same-version shape mutation.** Strengthening DDL requires a new schema version and explicit migration. Existing version-1 databases must not be reinterpreted through changed version-1 DDL.
4. **Single-writer migration.** Migration begins by acquiring the database write lock before reading migration-sensitive state.
5. **Atomicity.** Source validation, migration DDL/DML, target validation, and schema-version update occur in one transaction. Any exception or process termination before commit leaves the prior version intact.
6. **No implicit journal-mode mutation.** Ordinary opens and migrations do not change persistent SQLite journal mode as a side effect.
7. **No executescript inside the protected migration transaction.** Migration statements are executed individually so Python sqlite transaction behavior cannot end the intended transaction boundary.
8. **Deterministic migrations.** A migration is a pure function of the validated source database state and fixed migration code. It does not depend on wall-clock metadata, random IDs, network state, or external services unless the schema explicitly requires a separately frozen input.
9. **Re-open verification.** After commit, the database is reopened and the target version/shape is validated before the component is reported ready.
10. **Fail-closed integrity.** A migration never repairs unexplained tamper, missing required indexes, malformed rows, or incompatible identities by guessing. Such cases are surfaced as component-local recovery failures.

## Required migration sequence

For a migration from schema N to N+1:

1. open the database with bounded busy timeout;
2. acquire BEGIN IMMEDIATE;
3. read and validate PRAGMA user_version;
4. reject versions greater than the implementation's supported maximum;
5. validate the complete source schema-N shape and source-row invariants required by the migration;
6. execute explicit DDL/DML statements for N -> N+1;
7. validate the complete target schema-N+1 shape and migrated-row invariants;
8. update PRAGMA user_version=N+1;
9. validate the target version again while the write lock is still held;
10. commit;
11. close and reopen;
12. revalidate version and target shape before returning readiness.

If any step before commit fails, rollback is mandatory. If the process terminates, SQLite transaction recovery must leave either the complete old state or the complete new state, never a partially advertised migration.

## Multi-step upgrades

Code may support N -> N+K only as a sequence of individually defined adjacent migrations. Each adjacent migration must have:

- a source validator;
- a deterministic transformer;
- a target validator;
- explicit failure semantics;
- regression tests using a real database created by the previous released schema.

Skipping unknown intermediate versions is prohibited.

## Concurrency requirements

Migration and first-open initialization share one ownership model: only one writer may perform schema creation or migration at a time.

Concurrent callers must resolve to one of the following outcomes:

- one caller performs initialization/migration and commits; the others reopen/validate the resulting supported schema; or
- all callers fail with a stable component-level error if the database is incompatible or the bounded lock timeout is exhausted.

Expected contention must not leak raw SQLite uniqueness/schema-creation exceptions to higher-level ARK components.

## Crash-safety test matrix

Every migration implementation must test at least these interruption points:

- after source validation;
- after the first DDL change;
- after the first data transformation;
- after required indexes are created;
- after the schema-version field is updated but before commit.

After forced termination at each point, reopening with the old code or migration code must observe a valid old schema or a valid committed new schema. Partial target state must not be accepted.

## Data-integrity rules

Migration must preserve or recompute every deterministic identity and integrity field according to that store's contract.

Examples:

- Memory: owner/namespace/source -> memory ID, content digest, canonical metadata, revisions, timestamps, expiry semantics;
- Action Audit: request identity, argument digest, monotonic event ordering;
- durable authorization: token digest only, request binding, consumed state, expiry;
- Planner recovery: topology identity, event-chain hashes, independent tail anchor;
- proactive/self-improvement ledgers: deterministic record identity, revision CAS, event anchors.

A migration may not fabricate human review, model identities, hashes for unavailable bytes, evaluation results, or authorization decisions.

## Backup and destructive operations

A migration helper may support an optional user-requested backup, but backup creation is not authorization to overwrite or delete the source database.

Automatic destructive repair, database replacement, irreversible vacuum/erasure, or deletion of unsupported state requires the controlling user authorization if it would materially destroy recoverable information.

## Startup integration

Migration status is component-scoped. A failed Memory migration disables Memory and dependent Personal Context lanes; it does not by itself disable unrelated conversation or planner functionality. A failed Action Audit or durable-authorization migration disables write/action execution fail-closed while unrelated read-only lanes may remain available.

The startup coordinator must report component state and dependency-derived availability separately rather than collapsing all local state into one global boolean.

## Evidence required before source integration is considered complete

For each implemented migration:

- unit tests for source and target validation;
- same-version no-op reopen tests;
- unsupported-newer-version rejection;
- thread/process concurrent first-open and migration tests;
- exception rollback tests;
- process-termination crash tests;
- exact-head CI GREEN on supported operating-system/Python jobs;
- documentation of source schema, target schema, and recovery behavior.

Prototype-only results do not count as repository implementation evidence until matching source/tests land and exact-head CI passes.

## Boundaries unchanged

This contract does not authorize paid or external compute, real Candidate adapter/weight generation, protected/frozen V2 evaluation opening, automatic Candidate promotion, frozen-contract changes, destructive/irreversible operations, new credentials/account connections, physical-PC actions unavailable through authorized tools, or main merge.
