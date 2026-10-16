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
- normalized managed-table SQL needed to preserve required CHECK/UNIQUE constraints, non-index column collations, and `AUTOINCREMENT` semantics;
- absence of triggers on managed Memory tables unless explicitly defined by that schema version.

Unexpected generated/hidden columns or triggers fail closed. This prevents a same-version database from silently changing how private Memory data is stored or copied.

## Exact contract ingress

All public Memory constructors and store entry points must reject type-confused scope values before identity, SQL, or clock work. In particular:

- `MemoryWrite.scope`, `MemoryQuery.scope`, `MemoryRecord.scope`, and `MemoryEvent.scope` require an exact `MemoryScope` value;
- `deterministic_memory_id()`, `get()`, `delete()`, `events()`, and non-null `purge_expired(scope=...)` require the same exact scope type;
- persisted owner/namespace bytes are reconstructed into a validated exact `MemoryScope`; malformed stored scope is an integrity failure, never duck-typed or coerced input.

This keeps owner/namespace isolation and deterministic identity bound to one runtime contract instead of attribute-compatible substitutes.

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

Expected create/update/delete races are normalized to Memory domain conflicts. Before classifying a same-ID create as ordinary contention, the locked writer must validate both deterministic `memory_id` identity and the unique `(owner_id, namespace, source_id)` key; a persisted row that disagrees with either identity relation is integrity failure, not a normal create conflict.

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

## Coherent single-record and search reads

Expiry-sensitive `get()` and `search()` must bind one SQLite snapshot to one trusted time sample. The required order is:

`BEGIN read transaction -> execute a snapshot-establishing read -> sample trusted time exactly once while the transaction remains open -> fully validate/materialize rows from that snapshot -> apply expiry filtering -> close`.

The API does not promise the newest concurrent commit. It promises that a single result never combines an older clock sample with a newer database state, or an older database state with a newer clock sample. `include_expired=True` still uses the same snapshot discipline; it only skips the expiry filter.

## Coherent multi-namespace read

Personal Context uses the separate coherent-snapshot contract: one owner, ordered namespaces, one SQLite read transaction, one trusted expiry time, and fully materialized rows before transaction close.

## Acceptance tests

Repository tests should cover:

1. negative/newer schema version rejection;
2. partial version-zero database rejection;
3. generated column, unexpected trigger, missing/extra managed index, altered constraint, non-index `COLLATE`, and `AUTOINCREMENT` tamper rejection;
4. REAL-in-integer-column rejection without truncation;
5. NULL/malformed identity rejection;
6. content, metadata, deterministic-ID, and owner/namespace/source identity tamper rejection;
7. trusted-clock rollback rejection;
8. concurrent same-ID create and same-revision update yielding one winner;
9. refresh racing expiry cleanup without stale deletion;
10. false expire-event/count prevention when conditional delete affects zero rows;
11. coherent multi-namespace snapshot under a concurrent writer.

No destructive repair is implied. Corrupt or incompatible state remains preserved and component-local startup fails closed until an explicitly defined recovery path exists.
