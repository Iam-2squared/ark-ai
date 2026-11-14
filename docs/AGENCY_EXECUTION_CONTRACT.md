# ARK Agency Execution Contract

Work basis: `ab9f76d7b3306f8ec5a200c73756f31c8a0a6787`

This document fixes the reversible execution boundary shared by interactive tools, planner steps, proactive work, future computer control, and later multimodal-triggered actions. It does not connect a real action backend or authorize paid/external services.

## Pipeline

Every tool execution follows one ordered pipeline:

`resolve -> validate request -> authorize -> consume write approval -> pre-action audit -> execute -> record outcome -> verify if required`

A caller may not skip a stage because the request came from a trusted UI, planner, voice input, vision observation, scheduler, or previously successful action.

## Tool registry

The registry is the authority for mapping a tool name to its capability, effect class, and backend identity.

Required properties:

- registration is immutable after registry construction;
- duplicate tool names are rejected;
- lookup of an unknown tool fails closed;
- the resolved `ToolSpec.name` must equal `ToolCall.tool`;
- the resolved capability must equal `ToolCall.capability`;
- backend selection is bound to the registered tool, never inferred from model output;
- changing a tool's capability, effect, or backend requires a new registry construction/revision rather than in-place mutation.

The registry must expose read-only snapshots only. A caller cannot mutate registry internals through a returned mapping.

## Request identity

`ToolCall.request_id` is the canonical identity of one proposed action and binds:

- tool;
- capability;
- exact scope;
- canonical argument digest.

Raw arguments are not required in authorization or audit storage when the digest plus separately retained local request object is sufficient.

A modified argument, scope, capability, or tool produces a different request identity.

## Capability grants

A capability grant authorizes only an exact capability/scope pair and an optional trusted-clock expiry.

Rules:

- no prefix, wildcard, parent-scope, or semantic widening is implicit;
- expired grants fail closed;
- malformed persisted grants fail closed;
- a READ grant never upgrades into WRITE authority;
- model confidence, planner state, notification state, or prior success cannot create a grant.

## Durable one-shot authorization

WRITE effects require a durable request-bound one-shot authorization.

The durable ledger stores a cryptographic digest of the token identifier, never the plaintext token. Each row binds at least:

- token digest;
- request identity;
- expiry;
- consumed state/time;
- schema version/integrity fields required by the implementation.

Consumption requirements:

1. validate the persisted row and schema;
2. compare trusted time with expiry;
3. atomically consume exactly once;
4. commit consumption before backend execution;
5. never restore or reuse the token after audit or backend failure.

Concurrent consumers racing one token must produce exactly one successful consumption. Expected contention becomes a domain-level denial/conflict, not a leaked SQLite constraint/lock exception.

## Trusted clock

Authorization expiry and action timestamps come from an injected trusted clock owned by the execution boundary.

Callers may not supply arbitrary `now_ms` values to make an expired token appear valid. Invalid, negative, non-integer, or rollback-sensitive timestamps fail closed according to the persisted contract.

## Audit-before-action

Before any WRITE backend executes, a durable pre-action audit event must be committed successfully.

The pre-action event binds:

- request identity;
- tool/capability/scope;
- argument digest;
- authorization/decision outcome;
- trusted timestamp;
- correlation identity needed for later outcome reconciliation.

If audit persistence fails, the backend is not invoked. The already-consumed one-shot remains consumed.

READ operations also produce audit events when required by policy, but they do not require a write one-shot merely because they are audited.

## Backend execution

Backends implement typed registered tools only.

Rules:

- no dynamic shell/tool fallback for unknown tool names;
- no scope widening inside an adapter;
- no automatic credential discovery or account connection;
- no paid API/service invocation unless separately authorized by the user;
- no destructive/materially irreversible action outside its controlling explicit authorization;
- backend exceptions are surfaced as execution failure without making consumed authorization reusable.

A backend result does not prove the external side effect occurred exactly once. When the outcome is ambiguous, the request enters reconciliation state rather than automatic replay.

## Outcome recording and reconciliation

After backend return/failure, ARK records an outcome event correlated to the pre-action event and request identity.

At minimum, execution state distinguishes:

- denied before authorization;
- authorization consumed, audit failed;
- audit committed, backend not started;
- backend failed with known no-side-effect result;
- backend outcome unknown;
- backend reported success;
- postcondition verification succeeded/failed.

Unknown WRITE outcomes are not blindly retried. Reconciliation uses a safe READ observation or backend-specific idempotency mechanism where available.

## Planner integration

Planner state is not authorization.

A plan step may transition to RUNNING only when its dependencies and revision agree. Execution of the step then passes through this contract independently.

After restart, a recovered RUNNING WRITE step is ambiguous. It cannot cause automatic replay merely because the planner journal shows RUNNING.

## Proactive and multimodal integration

Proactive scheduler decisions, notifications, voice transcripts, vision observations, and UI events may propose or prepare a `ToolCall`. None of them create capability grants or one-shot authorization.

All such requests converge on the same registry, durable authorization, trusted-clock, audit, and backend boundary.

## Required implementation tests

Before a real WRITE adapter is connected, repository tests must cover at least:

- immutable registry snapshot and duplicate rejection;
- unknown tool/capability mismatch fail-closed;
- exact scope matching;
- durable one-shot restart/replay rejection;
- many concurrent consumers -> exactly one winner;
- expiry boundary with injected trusted clock;
- token plaintext absent from durable storage;
- audit failure -> backend not invoked;
- backend failure -> token remains consumed;
- READ execution without write one-shot;
- unknown backend outcome -> no blind retry;
- recovered RUNNING WRITE step -> no automatic replay.

## Integration rule

This contract is foundation work only. It does not change frozen V1/V2/Local UI/Launcher evidence, V3 Contract semantics, protected evaluation gates, Candidate state, promotion authority, or main-merge requirements. It authorizes no paid/external compute or service.
