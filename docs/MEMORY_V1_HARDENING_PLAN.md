# Memory v1 Hardening Plan

Status: same-version behavioral hardening plan for Draft PR #8. Existing schema-v1 DDL remains compatible; stronger DDL requires a later explicit migration.

Work basis: `53380a49e21e1c1ae594ff906da4602b9cfb9053`.

## Bootstrap and version validation

Memory startup should acquire `BEGIN IMMEDIATE` before deciding whether initialization is required.

Fail closed when:

- `PRAGMA user_version < 0`;
- `user_version` is newer than supported;
- version zero already contains any ARK-managed Memory table, index, or trigger;
- a supported version does not match its exact semantic schema fingerprint.

Fresh schema creation executes individual DDL statements inside the explicit transaction. Ordinary connections do not mutate persistent journal mode.

## Semantic schema fingerprint

Version validation must inspect more than `PRAGMA table_info`.

The validator should bind:

- `table_xinfo` column order/name/type/not-null/default/PK/hidden state;
- required indexes and their indexed columns/order/partial definition;
- absence of unrecognized indexes on managed objects when they can alter persistence semantics;
- normalized managed-table SQL needed to preserve required CHECK/UNIQUE constraints;
- absence of triggers on managed Memory tables unless explicitly defined by that schema version.

Unexpected generated/hidden columns or triggers fail closed. This prevents a same-version database from silently changing how private Memory data is stored or copied.

## Persisted row validation

SQLite affinity is not trusted as a type validator.

Before exposure or mutation, validate storage classes and values exactly:

- identity/scope/source are non-empty text and recompute to `memory_id`;
- content is text and matches `content_sha256`;
- metadata is valid canonical JSON under the Memory contract;
- created/updated/revision use integer storage class and valid domains;
- `updated_at_ms >= created_at_ms`;
- expiry is NULL or non-negative integer storage class;
- revision is an exact integer >= 1.

Readers must not silently repair REAL values using `int(...)`.

## Writer order

Mutation order is:

`write lock -> validate stored row -> trusted clock sample -> clock monotonicity check -> CAS mutation -> event -> commit`.

Expected create/update/delete races are normalized to Memory domain conflicts.

## Expiry cleanup

Expired rows are selected only after the write lock is held.

Each delete binds:

- memory identity;
- owner;
- namespace;
- observed revision;
- `expires_at_ms IS NOT NULL AND expires_at_ms <= trusted_now`.

An expire event and purge counter advance only when exactly one row was deleted.

A zero-row conditional delete is a stale candidate and produces no event/count. More than one affected row is integrity failure.

This rule also prevents malformed legacy NULL-primary-key rows from producing a false expire event/count when no row was deleted.

## Coherent multi-namespace read

Personal Context uses the separate coherent-snapshot contract: one owner, ordered namespaces, one SQLite read transaction, one trusted expiry time, and fully materialized rows before transaction close.

## Acceptance tests

Repository tests should cover:

1. negative/newer schema version rejection;
2. partial version-zero database rejection;
3. generated column, unexpected trigger, missing/extra managed index, and altered constraint rejection;
4. REAL-in-integer-column rejection without truncation;
5. NULL/malformed identity rejection;
6. content and metadata tamper rejection;
7. trusted-clock rollback rejection;
8. concurrent same-ID create and same-revision update yielding one winner;
9. refresh racing expiry cleanup without stale deletion;
10. false expire-event/count prevention when conditional delete affects zero rows;
11. coherent multi-namespace snapshot under a concurrent writer.

No destructive repair is implied. Corrupt or incompatible state remains preserved and component-local startup fails closed until an explicitly defined recovery path exists.
