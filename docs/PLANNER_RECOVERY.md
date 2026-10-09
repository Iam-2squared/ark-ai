# Planner Recovery Contract

Work basis: `53c92c677ba11f7ed4672ccf14c9e5d2f77ee069`

This document defines the reversible, local-first persistence boundary for ARK plan execution. It does not change frozen V1/V2/Local UI/Launcher evidence, V3 Contract semantics, protected evaluation gates, Candidate state, or main.

## Goal

Persist planner progress across process restarts without creating a second planner state machine or storing raw tool arguments.

`PlanGraph` remains the only transition authority. Persistence records an append-only journal of **explicit transition requests** that can reconstruct the same state deterministically, including any descendant blocking derived by `PlanGraph`.

## Identity and topology binding

A persisted plan binds:

- ordered step IDs;
- each step's canonical exact-`ToolCall.request_id`;
- each step's dependency tuple;
- a deterministic topology digest over the canonical representation.

Planner ingress must require exact `PlanStep` values, and each `PlanStep` must contain an exact `ToolCall`, not a subclass or duck-typed substitute. This keeps topology/action identity semantics stable before a topology digest is trusted.

Raw `ToolCall.arguments` are not stored in the planner journal. The request ID already binds their canonical digest through the action contract.

A plan identity must be deterministic for identical canonical topology and must not depend on Python hash/random iteration order.

## Explicit transition journal

The journal records externally requested planner transitions, not a separate event for every internal descendant state change.

Each journal record binds:

- plan identity and topology digest;
- step ID;
- exact requested `from_state` and `to_state`;
- expected revision and resulting revision for the explicitly transitioned step;
- occurrence time from the injected trusted clock;
- canonical digest of the complete **post-transition planner status snapshot**;
- previous event digest;
- current event digest.

When an explicit non-success terminal transition causes `PlanGraph` to derive descendant `BLOCKED` states, those derived changes are captured by the post-state digest. They are **not** journaled again as synthetic public transitions.

This prevents recovery from double-applying descendant blocking while still detecting planner-logic drift, missing derived state, or a corrupted status snapshot.

## Hash chain and independent tail anchor

The event digest forms an append-only SHA-256 chain. Modified, reordered, duplicated, or middle-deleted events fail closed during replay.

A hash chain alone cannot prove that the newest suffix was not truncated. The durable planner therefore also maintains an independent tail anchor, updated atomically with every appended journal event, binding at minimum:

- plan identity and topology digest;
- committed event count;
- last event ID;
- last event digest;
- maximum trusted occurrence timestamp observed for that plan.

Recovery must reject an event stream whose count or tail does not match the independent anchor. The anchor must not be reconstructed from the same possibly-truncated event stream and then treated as evidence.

## Recovery

Recovery must:

1. validate the database schema version and required table/index shape;
2. validate the persisted topology digest against the supplied exact-typed `PlanGraph`;
3. validate the independent tail anchor against the stored journal;
4. replay explicit journal entries in event order through the planner's public transition API;
5. require exact explicit-step state/revision agreement at each event;
6. recompute the complete post-transition status digest after each replayed event and require equality with the journal;
7. reject clock rollback and malformed persisted values;
8. expose an interrupted `RUNNING` step as ambiguous rather than silently retrying or marking it successful.

Recovery never performs a tool action. It only reconstructs planner state.

## Concurrency

First-open initialization and same-revision transition append operations must serialize with an explicit SQLite write transaction. Concurrent callers racing the same planner revision must yield exactly one committed transition; losers receive a domain-level conflict rather than a partial write or SQLite implementation error.

The journal append and independent tail-anchor update are one atomic transaction. A committed event without its matching anchor update, or an anchor that advances without its event, is invalid state.

Persistent journal mode must not be mutated on every connection open. Bootstrap/schema inspection must follow the same concurrency discipline documented in `SQLITE_DURABILITY_FINDINGS.md`.

## Safety boundary for RUNNING actions

A recovered `RUNNING` state is not evidence that a side effect completed. Later action integration must resolve that ambiguity through durable registry-bound action identity, execution-occurrence state, audit records, and backend-specific idempotency/reconciliation rules.

Therefore recovery must never automatically:

- re-execute a write-effect action;
- mark a recovered `RUNNING` action as succeeded;
- consume or mint a new authorization token;
- infer external-world success from planner state alone.

## Integration order

1. land exact `PlanStep` ingress, exact nested `ToolCall`, immutable topology/status snapshots, and exact transition-type validation;
2. propagate all non-success terminal dependency outcomes to pending descendants and freeze focused regressions;
3. add deterministic topology and canonical full-status digest helpers;
4. add the SQLite explicit-transition journal with strict schema validation;
5. add the independent atomic tail anchor;
6. add replay-only recovery tests, including derived descendant blocking and tail truncation;
7. add concurrent first-open and same-revision transition stress tests;
8. integrate with durable one-shot authorization and action audit using mock/disconnected backends only.

This foundation is not a roadmap PASS and does not authorize real computer control, paid/external compute, Candidate work, protected evaluation opening, promotion, or main merge.
