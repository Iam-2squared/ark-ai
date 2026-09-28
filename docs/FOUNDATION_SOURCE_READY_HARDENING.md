# Foundation Source-Ready Hardening Queue

Status: implementation-preparation note for Draft PR #8. This is not PASS evidence.

## Planner

The next executable patch is intentionally narrow:

- require ordered dependency input and canonicalize it to tuple;
- expose immutable topology snapshots;
- make transition rules immutable;
- require exact `StepState` transition values;
- require exact non-bool non-negative revisions;
- use sorted traversal where registration order must not affect derived state.

Matching tests must cover set/frozenset/generator dependency rejection, raw-string state rejection, bool/negative revision rejection, topology immutability, status snapshot immutability, and transitive blocking.

## SQLite Memory

Preserve schema-v1 DDL compatibility while tightening behavior:

- serialize bootstrap with a write transaction before schema inspection;
- reject negative/newer schema versions and partial version-0 managed schemas;
- validate managed tables/indexes/triggers with exact schema fingerprints;
- validate persisted row storage classes and deterministic identity before conversion;
- sample trusted mutation time after the write lock;
- normalize create/CAS contention to domain conflicts;
- perform expiry cleanup with scope + revision + expiry-bound DELETE predicates and count only actual deletions;
- materialize read/search snapshots before trusted-time expiry filtering.

## Action Audit

Keep v1 compatibility first, then introduce any stronger schema through an explicit migration:

- serialized bootstrap and same-version schema validation;
- persisted event validation before exposure or append;
- write lock before trusted clock sampling;
- monotonic append time against the persisted tail;
- explicit v1-to-v2 migration for chain/anchor integrity rather than silent same-version DDL mutation.

## Execution safety chain

After the persistence primitives are GREEN:

1. immutable ToolRegistry with stable registration identity;
2. restart-safe one-shot authorization ledger storing only a token digest;
3. atomic authorization consumption plus execution-occurrence creation;
4. pre-action audit persistence before mock backend dispatch;
5. durable distinct outcomes for known-no-effect, outcome-unknown, and reported-success;
6. planner recovery journal and startup component readiness integration.

No item here authorizes paid/external compute, real Candidate generation, protected evaluation opening, promotion, frozen-contract changes, destructive work, new credentials, or main merge.
