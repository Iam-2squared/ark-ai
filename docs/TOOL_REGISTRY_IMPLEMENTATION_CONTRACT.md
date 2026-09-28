# Tool Registry Implementation Contract

Status: reversible foundation specification for Draft PR #8.

## Goal

ARK needs one immutable runtime mapping from a tool name to its declared capability, effect, stable backend identity, and backend implementation.

## Registration

Each registration binds:

- tool name;
- capability;
- effect;
- stable backend ID;
- backend object implementing the execution protocol.

Construction snapshots the inputs, rejects duplicate names, sorts by tool name, freezes the mapping, and calculates one deterministic registry revision. Registration order must not change that revision.

The revision payload binds schema version, tool name, capability, effect, and backend ID. Python object addresses and construction order are excluded.

## Registry-bound action identity

`ToolCall.request_id` intentionally identifies the proposed request bytes, but it does not by itself
bind the runtime registry revision, effect classification, or backend identity. Durable execution
state therefore requires a second identity.

For a resolved registration, compute a deterministic registry-bound action identity from:

- canonical `request_id`;
- exact registry revision;
- tool name;
- capability;
- effect;
- stable backend ID.

Changing capability, effect, backend ID, or any registry member that changes the revision must
change this bound identity even when the original request bytes are unchanged.

Durable one-shot authorization, execution-occurrence rows, pre-action audit correlation, planner
execution context, and restart recovery must bind this registry-bound identity. A pending or
recovered action whose recorded registry revision no longer matches the active immutable registry
must fail closed and require a new proposal/authorization rather than being silently reinterpreted.

This separation preserves `request_id` as a useful grouping key for equivalent proposed request
content while preventing old authorization from surviving a tool-semantics or backend change.

### Registry-binding tests required

- same request + same registry/spec -> same bound identity;
- same request + READ/WRITE effect change -> different bound identity;
- same request + backend-ID change -> different bound identity;
- same request + capability change -> different bound identity;
- unchanged request under a different registry revision -> different bound identity;
- stale durable authorization/recovery state from an older revision -> fail closed;
- two separately authorized executions of one request retain distinct execution-occurrence IDs.

## Resolution

Lookup is exact by tool name. Unknown names fail closed. There is no fuzzy matching or dynamic fallback.

The returned registration is read-only. Changing capability, effect, or backend identity requires construction of a new registry and therefore a new revision.

The registry chooses the eligible backend but does not grant permission. Existing capability/scope and write-authorization checks still apply after resolution.

## Tests required

Repository tests should cover:

- duplicate-name rejection;
- unknown-name rejection;
- malformed registration rejection;
- immutable registry snapshots;
- 100+ randomized registration orders yielding one revision;
- capability/effect/backend-ID changes yielding different revisions;
- lookup causing no backend execution.

## Integration order

Registry source/tests should land before durable action authorization and the disconnected executor are integrated. Real action adapters remain disconnected until the full local safety chain is GREEN.

This document changes no frozen evidence, V3 Contract, Candidate state, protected evaluation gate, or main-merge authority.
