# Persisted Event Validation Contract

Status: reversible local-first foundation specification for Draft PR #8.

## Rule

SQLite column affinity and application dataclasses do not make persisted rows trustworthy. Every persisted event is validated before it is returned, used for recovery, or used as an ordering anchor.

This applies to Memory lifecycle events, action-audit events, planner journal events, proactive scheduler records, and later local observability traces.

## Exact value requirements

Before conversion:

- integer fields must already have SQLite integer storage class and must satisfy exact non-bool range rules;
- text fields must already be text, non-blank where required, and satisfy their canonical syntax;
- digests and deterministic IDs must be recomputed or syntax-checked according to their owning contract;
- enum/state values must be exact allowed values;
- timestamps must be non-negative and obey any required monotonic ordering;
- revisions/event IDs must be positive exact integers;
- optional values must be either NULL or the exact required storage class.

Readers must not use `int(...)`, `str(...)`, or enum construction as silent repair of malformed persisted data.

## Event-specific integrity

Memory lifecycle events bind memory ID, exact owner/namespace, operation, revision, and trusted time. The event cannot widen or invent scope.

Action-audit events bind canonical request identity, tool, capability, scope, argument digest, outcome, and trusted time. Request identity is recomputed from persisted canonical fields before exposure.

Planner journal events bind plan/topology identity, step, before/after revision, typed state transition, event sequence, and chain/anchor integrity.

## Ordering

Where event order is semantically meaningful, mutation time is sampled only after the SQLite write lock is acquired. Recovery rejects timestamp rollback when the owning contract requires monotonic trusted time.

Event sequence order and timestamp order are separate fields and are both validated; one is not silently substituted for the other.

## Failure behavior

A malformed persisted event blocks only the owning component/lane where startup-readiness isolation permits it. It is never silently skipped to make the store appear healthy.

Diagnostics report stable failure codes and content-free identities rather than copying private payloads.

## Required tests

- REAL values in integer-affinity columns are rejected rather than truncated;
- negative/zero revisions and event IDs are rejected where forbidden;
- malformed deterministic IDs/digests fail closed;
- invalid enum/operation strings fail closed;
- timestamp rollback is rejected where monotonicity is required;
- scope/request identity tampering is rejected;
- one malformed row cannot be silently omitted from recovery history.

This contract changes no frozen evidence, V3 Contract, protected evaluation gate, Candidate state, or main-merge authority.
