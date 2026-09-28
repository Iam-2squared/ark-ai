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

## Deterministic reference vectors

These values are derived only from canonical JSON and are safe, offline implementation fixtures.

For the existing two-tool registry fixture, the registry revision is:

`tools_e3fec8092546d8f7a67eee140d90ca4fcb076965953031ec176d5be4a605f146`

For request `files.write / files.write / workspace:a / {"path":"x"}`:

- request ID: `act_2d08b6d18b9952951d04d23cfb91e3ea5d2a23f8985e97bf8a7e07d5c64d0481`;
- base bound ID: `bound_e1ede52438411a87e0287186be607d5b501e4aeda0e7522d821ca61f8b7af8b5`;
- changing only effect from `write` to `read` produces registry revision
  `tools_9744ae49950aa0b1fb4352d8c793e4e44073ed53793eefbc182f47b5728e7440` and bound ID
  `bound_2e1475a7c01966dca009cd1e011f1131afcf9b158e5c48349283646a81b8cd9c`;
- changing only backend ID from `mock.files.write:v1` to `mock.files.write:v2` produces registry
  revision `tools_21aef4d413d7866c560d1d50a32dceead3e8c4d2698f4eba1082230b55fb4a04`
  and bound ID
  `bound_4699d5177e68fcfcf4811f7731167a0eadd7352a2d92b0689a250a36a835d5ad`.

Implementations must reproduce these values before durable authorization/recovery integration.

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
