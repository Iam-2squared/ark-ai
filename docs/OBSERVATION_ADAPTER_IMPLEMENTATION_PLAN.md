# Observation Adapter Implementation Plan

Status: reversible local-first implementation plan for Draft PR #8. This is not roadmap PASS evidence.

Work basis: `ddc75235a41bf93a741bfa308d28c259f3efe623`.

## Goal

Extend the existing typed `ObservationEnvelope` with deterministic fixture adapters before any live microphone, camera, desktop capture, or external model dependency is introduced.

## Adapter interface

A fixture adapter should have one stable adapter identity/version and accept only already-provided local fixture bytes plus explicit source/privacy metadata.

The adapter computes the content digest itself and returns an `ObservationEnvelope`. Callers do not supply a trusted digest for bytes the adapter can hash directly.

Derived adapters may create a transcript or structured observation from a parent fixture. The derived envelope records the parent content digest and uses a distinct adapter identity.

## Initial fixture adapters

1. text fixture -> TEXT observation;
2. transcript fixture -> TRANSCRIPT observation with optional parent digest;
3. image fixture -> IMAGE observation carrying only digest/provenance metadata;
4. screen fixture -> SCREEN observation carrying only digest/provenance metadata.

No raw fixture bytes are embedded into the envelope.

## Determinism

For identical fixture bytes, source metadata, adapter identity, privacy scope, and trusted ingest time, repeated adaptation produces the same observation identity.

Changing any bound field changes the identity.

## Retention boundary

The adapter owns no long-term media retention policy. Fixture bytes may exist in test data, while downstream provenance uses digests and explicit local references.

A later persistent media store requires its own retention/deletion contract before live capture is connected.

## Tests required

Repository tests should cover:

- deterministic fixture hashing;
- all four observation kinds;
- adapter-generated digest rather than caller-trusted digest;
- parent-digest lineage for a derived transcript;
- privacy/source metadata binding;
- no raw fixture bytes in the envelope representation;
- malformed source/privacy metadata rejection;
- repeated fixture adaptation producing identical observation identity.

## Integration order

1. land matching tests for the existing ObservationEnvelope;
2. add fixture-only adapters;
3. expose fixture observations to observability/evaluation and local UI development paths;
4. connect Personal Context only through explicit provenance;
5. keep live capture and hardware adapters out of scope until local privacy/retention and execution foundations are integrated.

No external service, live device capture, paid compute, Candidate generation, protected evaluation opening, or main merge is authorized by this plan.
