# Action Audit v1 -> v2 Migration Plan

Status: explicit local migration plan for Draft PR #8. This does not change the current v1 schema until source/tests land.

Work basis: `6c679525654912ac2a3659b3efb246c9e5e51def`.

## Why a new schema version is required

The current v1 Action Audit stores independent rows. Adding chain and tail-anchor integrity changes durable semantics and must not be introduced as an unversioned v1 mutation.

v2 therefore uses an explicit adjacent migration.

## Source validation

Before migration, v1 must pass:

- exact supported v1 schema/index shape;
- exact persisted storage-class checks;
- canonical request identity recomputation from tool, capability, scope, and argument digest;
- valid outcome vocabulary for the migration policy;
- valid event IDs and timestamps.

Malformed history is rejected rather than repaired.

## Deterministic migration

Migration acquires one write transaction before inspecting the source.

For each v1 event in event-ID order, v2 computes a deterministic event digest from the validated legacy fields plus the previous digest.

Legacy timestamps are preserved exactly. The migration does not rewrite historical time to make it monotonic.

The v2 anchor records:

- event count;
- final event ID;
- final event digest;
- maximum historical timestamp observed in the migrated log.

The maximum historical timestamp becomes the lower bound for future trusted append times without altering legacy rows.

## Commit boundary

Source validation, v2 table/index creation, deterministic row transformation, anchor creation, target validation, and schema-version update occur in one transaction.

Any exception or process termination before commit must leave a valid v1 database.

After commit, reopen and validate the complete v2 chain plus anchor before the component can report ready.

## Concurrency

Concurrent callers starting from one v1 database must converge on exactly one migration. Other callers reopen and validate v2.

No caller may run a second migration over already-committed v2 state.

## v2 recovery checks

Reopen validation rejects:

- modified event fields;
- missing or reordered interior events;
- tail truncation;
- anchor modification;
- request identity mismatch;
- event-digest mismatch;
- future append time below the anchor's maximum historical time.

## Acceptance matrix

Required repository tests:

1. empty and populated v1 migration;
2. legacy non-monotonic timestamps preserved byte-for-value;
3. deterministic v2 result from the same validated v1 bytes;
4. exception rollback at multiple migration phases;
5. forced process termination before commit -> valid v1 on reopen;
6. concurrent migration callers -> one migrator, remaining callers cleanly reopen v2;
7. event edit, interior deletion, tail deletion, and anchor edit -> reject;
8. new v2 append below historical maximum time -> reject;
9. source v1 tamper -> no migration attempt.

No real backend connection, paid service, external compute, Candidate work, protected evaluation opening, or main merge is authorized by this plan.
