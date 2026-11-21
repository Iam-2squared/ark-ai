# Run1089 — Rebase Observation fixture ingress guards onto the latest foundation

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent HEAD: `073d08ca19dfc67de7dd8da6ce3956bbefc3974b`.
- Original PR #107 base: `b585c61a6e3ca1a9f456175b2a96053a908a500c`.
- Compare evidence: the intervening parent changes did not modify either of the two Observation fixture test paths or their evidence-note paths. This rebase adds only those four files; no production adapter or frozen Observation Envelope v1 contract is changed.
- Child branch: `research/run1089-observation-fixture-guard-rebase`.

## Reapplied coverage

- Four fixture adapters (text, transcript, image and screen) reject payloads exceeding the 4 MiB byte budget before private hashing; UTF-8 byte length, not character count, governs text.
- Exact-budget text and binary fixtures remain digest-only envelopes with no raw payload field.
- Metadata validation rejects non-exact types, malformed UTF-8, NUL/control/bidi formatting, boolean timestamps and invalid parent digests before private hashing.
- Rebound digest entrypoints are rejected before receiving private fixture bytes.

All test data is synthetic and in-memory. No camera, microphone, screen, filesystem, network, notification or ToolBackend is accessed.

## Exact-head evidence carried forward

Original PR #107 exact head `83ef4867a219e097abacbe3123df52f7c0f28e38` passed CI run [44805089705](https://github.com/Iam-2squared/ark-ai/actions/runs/44805089705), GREEN 6/6. This result applies only to that original head. The rebase requires fresh exact-head Windows/Linux × Python 3.11–3.13 CI.

## Limits

This validates local fixture ingress bounds and hash ordering only. It does not authenticate a source, establish consent, enable live capture, prove provenance, trusted time, independent custody, or authorize dispatch. Observation Envelope v1 and production adapter source remain unchanged.

No paid/external compute, Candidate, protected V2 evaluation, frozen-contract change, credentials, physical hardware, UI/frontend work or main merge. **ARK/JARVIS remains NOT_PASSED.**
