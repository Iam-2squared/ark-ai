# ARK Multimodal Input Contract

This document defines reversible contracts for future Voice and Vision inputs. It adds no microphone, camera, screen-capture, cloud model, or external-service dependency.

## Boundary

Voice and Vision are observation adapters. They may produce typed local observations for reasoning, memory, or planning, but they never grant permission and never execute actions directly.

`sensor/input -> local adapter -> typed observation -> provenance -> policy-aware consumer`

Any effectful follow-up still passes through the common ToolRegistry, exact capability/scope checks, durable one-shot authorization for writes, pre-action audit, and ActionExecutor boundary.

## Observation identity

Every observation should carry a deterministic envelope with:

- observation type and schema version,
- local source identifier,
- capture/ingest time from a trusted clock,
- content digest,
- optional parent/source digest for derived observations,
- explicit privacy/scope label,
- adapter identity/version.

Raw media bytes are not required in downstream provenance when a digest and a retained local source reference are sufficient.

## Voice

A future voice adapter should separate:

1. audio capture,
2. speech-to-text,
3. speaker/source metadata,
4. intent interpretation.

Transcription is untrusted model output. It cannot authorize actions, modify grants, or bypass one-shot approval. Ambiguous or low-confidence speech may remain an observation without action.

No cloud speech API, paid transcription, always-on microphone capture, or account connection is implied by this contract.

## Vision

A future vision adapter should separate:

1. image/screen/frame capture,
2. object/text/layout perception,
3. structured observation extraction,
4. downstream reasoning.

Vision output is untrusted model output. Detected buttons, windows, text, faces, credentials, or UI affordances do not themselves grant permission to interact with them.

No camera activation, screen recording, remote vision API, or external upload is implied by this contract.

## Privacy and retention

- Capture must be explicitly scoped to an allowed local source.
- Downstream storage follows the ARK privacy/data-lifecycle contract.
- Raw media retention must be explicit; absence of a retention rule does not mean permanent retention.
- Derived memories remain owner/namespace isolated.
- Provenance should prefer content digests and local references over duplicating sensitive plaintext or media.

## Determinism and replay

Where deterministic replay is required, tests should use fixture observations or mock adapters. CI must not depend on live microphones, cameras, desktops, external APIs, or paid services.

## Integration rule

Multimodal adapters stay disconnected from real actions until the planner, memory integrity, ToolRegistry, durable authorization, action audit, and mock ActionExecutor foundations are integrated and GREEN. This groundwork is not a roadmap PASS and does not authorize real device control, paid/external compute, Candidate generation, protected evaluation opening, promotion, frozen-contract changes, new credentials, destructive actions, or main merge.
