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
