# ARK Durable State Integrity Contract

Work basis: `96cf5ac5ad925f312f1654d622c6edfbe6466840`

This contract defines the shared local-first persistence invariants for Memory, Action Audit, durable one-shot authorization, planner recovery, proactive scheduler state, and future local durable foundations. It is reversible foundation work only and changes no frozen evaluation or authorization boundary.

## Connection and bootstrap

Every SQLite-backed component must follow the same startup rules:

- ordinary connection open may set connection-local options such as `busy_timeout`, but must not repeatedly mutate persistent journal mode;
- first-open schema inspection and creation are serialized by an explicit write transaction;
- acquire `BEGIN IMMEDIATE` before deciding whether schema creation or migration is required;
- do not rely on `executescript()` to preserve an already-acquired transaction boundary;
- create schema objects with individual statements inside the explicit transaction;
- set `PRAGMA user_version` only after all objects for that version exist;
- rollback the whole bootstrap transaction on any failure.

Concurrent first-open callers must converge on one valid schema without leaking expected `table already exists`, lock, or constraint failures to callers.

## Supported-version validation

A matching `user_version` is necessary but not sufficient.

On every open, implementations must validate the required table and index shape for the supported version. Validation must preserve compatibility with the exact historical DDL for that version. Stronger constraints that change the observable schema require an explicit migration/version bump rather than silently redefining an existing version.

Missing tables, columns, required indexes, incompatible declared types, or unsupported newer versions fail closed.

## Mutation transaction order

Durable mutations follow:

`acquire write lock -> validate persisted state -> sample trusted clock -> validate time -> perform CAS/mutation -> append correlated event/anchor -> commit`

The trusted mutation timestamp is sampled after the write lock is acquired. This prevents a worker that waits on the lock from later committing a timestamp that predates an already-committed competing mutation.

Caller-supplied timestamps do not become trusted merely because they are well-typed.

## Compare-and-swap

Revision-sensitive state uses exact non-bool integer revisions.

Expected contention must resolve to domain-level conflict/denial outcomes. Raw SQLite uniqueness, lock, or stale-update errors are not the public concurrency contract.

Create races, same-revision updates, one-shot consumption, planner transitions, and proactive prepare decisions must produce exactly-one or at-most-one winners according to their component contract.

## Persisted row integrity

Persisted data is untrusted input after restart.

Before surfacing or mutating a row, validate all fields needed to establish its identity and semantics, including as applicable:

- deterministic identity recomputation;
- exact owner/namespace or scope binding;
- canonical serialized metadata;
- content or argument digests;
- exact enum/type constraints;
- non-negative revision and timestamp domains;
- creation/update ordering;
- expiry representation;
- schema/integrity version fields.

Integrity failure is not repaired by guessing. The operation fails closed and surfaces a typed integrity/schema error.

## Canonical serialization

Any digest-bound structure uses one canonical serialization with explicit encoding, stable key ordering, and rejection of NaN/infinity where JSON semantics are used.

Equivalent logical payloads must produce the same digest. A changed scope, content, arguments, topology, policy revision, or other bound field must change the relevant identity.

## Expiry and deletion

Expiry cleanup may not act on a stale pre-lock snapshot.

Use either a write lock before selecting candidates or a conditional delete bound to the observed revision and expiry predicate; high-risk lifecycle paths should use both when practical.

Emit an expiry/deletion event only for rows actually deleted. Physical deletion semantics remain explicit and testable.

## Append-only journals and anchors

A hash chain detects modification and interior deletion only when the full expected tail is known. Therefore journals whose recovery integrity depends on append-only history must persist an independent anchor in the same transaction, containing at least:

- event count;
- last event identity;
- last event digest;
- last trusted timestamp when monotonic time is part of the contract.

Recovery verifies both the chain and the anchor. Editing, reordering, interior deletion, and tail truncation must fail closed.

## Authorization durability

One-shot authorization storage persists only a cryptographic token digest, never bearer-token plaintext. Consumption commits before any external or mock write backend is invoked and remains consumed after later audit/backend failure.

Restart and concurrent consumers must not permit replay.

## Crash and ambiguous-outcome semantics

A committed local state transition does not prove an external side effect occurred. Durable action state must distinguish pre-action audit success, backend known failure, backend unknown outcome, reported success, and verification outcome.

Unknown write outcomes are reconciled; they are never blindly replayed.

## Privacy

Durable state should contain the minimum data needed for integrity, recovery, and explanation.

Do not duplicate Memory plaintext into audit/scheduler metadata, store raw tool arguments when a digest suffices, persist one-shot bearer tokens, or retain raw media without a separate explicit retention contract.

## Required concurrency evidence

Before a durable component is treated as integration-ready, tests should include:

- repeated concurrent first-open;
- repeated same-revision or same-token contention;
- restart/reopen verification;
- same-version schema tamper rejection;
- persisted-row tamper rejection;
- trusted-clock rollback rejection where timestamps govern semantics;
- process-level contention for the highest-risk SQLite paths.

Evidence applies only to the exact saved implementation/HEAD tested.

## Integration rule

These rules do not authorize paid/external compute, real Candidate generation, protected/frozen V2 evaluation opening, Candidate promotion, frozen-contract changes, new credentials/account connections, destructive actions, physical hardware actions unavailable through authorized tools, or main merge.
