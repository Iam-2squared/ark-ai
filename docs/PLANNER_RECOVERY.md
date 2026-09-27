# Planner Recovery Contract

Work basis: `15fdfd881ac7399c457237a20bc6fea4ee7056d6`

This document defines the reversible, local-first persistence boundary for ARK plan execution. It does not change frozen V1/V2/Local UI/Launcher evidence, V3 Contract semantics, protected evaluation gates, Candidate state, or main.

## Goal

Persist planner progress across process restarts without creating a second planner state machine or storing raw tool arguments.

`PlanGraph` remains the only transition authority. Persistence records an append-only transition journal that can reconstruct the same state deterministically.

## Identity and topology binding

A persisted plan binds:

- ordered step IDs;
- each step's canonical `ToolCall.request_id`;
- each step's dependency tuple;
- a deterministic topology digest over the canonical representation.

Raw `ToolCall.arguments` are not stored in the planner journal. The request ID already binds their canonical digest through the action contract.

A plan identity must be deterministic for identical canonical topology and must not depend on Python hash/random iteration order.

## Journal invariants

Each transition record binds:

- plan identity and topology digest;
- step ID;
- exact `from_state` and `to_state`;
- expected revision and resulting revision;
- occurrence time from the injected trusted clock;
- previous event digest;
- current event digest.

The event digest forms an append-only SHA-256 chain. Missing, reordered, duplicated, or modified events make recovery fail closed.

## Recovery

Recovery must:

1. validate the database schema version and required table/index shape;
2. validate the persisted topology digest against the supplied `PlanGraph`;
3. replay journal entries in event order through the planner's public transition API;
4. require exact state/revision agreement at each replayed event;
5. reject clock rollback and malformed persisted values;
6. expose an interrupted `RUNNING` step as ambiguous rather than silently retrying or marking it successful.

Recovery never performs a tool action. It only reconstructs planner state.

## Concurrency

First-open initialization and same-revision transition append operations must serialize with an explicit SQLite write transaction. Concurrent callers racing the same planner revision must yield exactly one committed transition; losers receive a domain-level conflict rather than a partial write or SQLite implementation error.

Persistent journal mode must not be mutated on every connection open. Bootstrap/schema inspection must follow the same concurrency discipline documented in `SQLITE_DURABILITY_FINDINGS.md`.

## Safety boundary for RUNNING actions

A recovered `RUNNING` state is not evidence that a side effect completed. Later action integration must resolve that ambiguity through durable request identity, audit records, and backend-specific idempotency/reconciliation rules.

Therefore recovery must never automatically:

- re-execute a write-effect action;
- mark a recovered `RUNNING` action as succeeded;
- consume or mint a new authorization token;
- infer external-world success from planner state alone.

## Integration order

1. land immutable planner topology/status snapshots and exact transition-type validation;
2. add deterministic topology identity helpers;
3. add the SQLite journal with strict schema validation;
4. add replay-only recovery tests;
5. add concurrent first-open and same-revision transition stress tests;
6. integrate with durable one-shot authorization and action audit using mock/disconnected backends only.

This foundation is not a roadmap PASS and does not authorize real computer control, paid/external compute, Candidate work, protected evaluation opening, promotion, or main merge.
