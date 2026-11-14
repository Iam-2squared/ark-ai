# Observability Occurrence-Binding Addendum

Status: reversible local-first addendum for Draft PR #8. This refines correlation semantics before source instrumentation lands.

Work basis: `d7a7cb15980cc875a7c1594d706904f88dcafa6b`.

## Problem

A canonical `ToolCall.request_id` groups equivalent proposed request content, but the same request may be separately authorized and legitimately executed more than once.

Using `request_id` alone as the primary action-trace correlation key would collapse distinct execution occurrences and make restart/reconciliation evidence ambiguous.

## Action correlation rule

For action execution observability:

- `execution_id` is the primary correlation identity for one concrete execution occurrence;
- `request_id` is a grouping identity for equivalent proposed request content;
- `bound_action_id` binds the request to the exact immutable Tool Registry revision/effect/backend semantics;
- planner step/plan identities are parent workflow references, not substitutes for execution identity.

Pre-action audit, dispatch, backend result, verification, and reconciliation events for one occurrence all bind the same `execution_id`.

Two separately authorized executions of the same canonical request must have distinct `execution_id` values while retaining the same `request_id` when request bytes are identical.

## Minimal action event envelope

A content-minimized action event should bind:

- schema version;
- event type;
- component and component revision;
- `execution_id`;
- `request_id`;
- `bound_action_id`;
- trusted event timestamp;
- typed outcome category;
- optional parent event identity.

Raw arguments, bearer tokens, Memory plaintext, and backend secrets are excluded.

## Deterministic identity

Event identity is SHA-256 over canonical structured metadata. Equivalent fields produce the same event identity regardless of mapping insertion order.

A local prototype verified:

- one event identity across **1,000 randomized mapping orders**;
- changing only `execution_id` changed the event identity;
- changing only `request_id` changed the event identity.

Reference base vector:

`evt_dffc2bdbbcc61f881120128067aa9dde983b0046211d360955309f9749bd4a00`

Changing only the execution occurrence produced:

`evt_e409989f86123e292e6cf69c17de690a06196e71d265a8d308faad24baec4677`.

## Recovery interpretation

A recovered action trace must never infer success from the presence of a request-level event belonging to another occurrence.

If an occurrence reached dispatch but lacks a trustworthy terminal/verification event for its own `execution_id`, it remains outcome-unknown according to the durable action-recovery contract.

## Integration

This addendum should be applied when local observability source is implemented and when the existing observability contract is next updated normally.

It changes no action authority. Correlation identities are not capability grants or authorization tokens.

No external telemetry, paid service, real computer action, Candidate generation, protected evaluation opening, frozen-contract change, promotion, or main merge is authorized.
