# ARK Typed Observation Envelope

Work basis: `cca0308185885003c13e74807176c0510d78ada2`

This contract defines the common local envelope for future voice, vision, UI, and other observation adapters. It adds no live microphone/camera capture and no external service.

## Required fields

A typed observation contains:

- schema version;
- observation kind;
- local source identifier;
- trusted capture/ingest time;
- content SHA-256;
- adapter identity/version;
- explicit privacy scope;
- optional parent/source digest for derived observations.

The envelope contains references and digests, not raw media by default.

## Deterministic identity

`observation_id` is derived from the canonical serialization of the required fields above.

Equivalent envelopes produce the same ID. A changed content digest, capture time, source, adapter, kind, privacy scope, or parent digest produces a different ID.

The identifier is provenance only. It is never a capability grant or authorization token.

## Validation

Implementations fail closed on:

- unknown or raw-string observation kinds when a typed enum is required;
- blank source/adapter/privacy identifiers;
- bool, negative, or non-integer timestamps;
- malformed content or parent digests;
- unsupported schema versions;
- derived observations whose declared parent digest is malformed.

## Adapter boundary

Adapters convert local input into observations. They do not own action policy.

Examples:

- a voice adapter may emit a transcript observation derived from an audio digest;
- a vision adapter may emit a structured screen observation derived from a frame digest;
- a UI adapter may emit a user-input observation.

Downstream reasoning may use these observations to retrieve context or prepare plans. Any side effect still passes through the common registry, permission, durable authorization, audit, and execution boundary.

## Retention

Raw media retention is separate from observation retention.

An observation may retain a local source reference and digest while raw media is ephemeral. If raw media is persisted, its purpose, scope, lifetime, and physical deletion behavior must be explicit under the privacy/data-lifecycle contract.

## Fixture-first testing

Initial implementation should use deterministic fixtures and mock adapters.

Required tests:

- deterministic identity for equivalent envelopes;
- identity changes when any bound field changes;
- exact-type kind/timestamp checks;
- malformed digest rejection;
- privacy/source isolation;
- parent-digest lineage for derived observations;
- no raw media bytes embedded in the envelope;
- observations cannot manufacture action authorization.

Live microphones, cameras, desktops, cloud APIs, and paid services are not CI dependencies.

## Integration rule

This envelope is reversible groundwork only. It changes no frozen V1/V2/Local UI/Launcher evidence or V3 Contract/evaluation boundary and authorizes no real device action, Candidate work, promotion, paid/external compute, or main merge.
