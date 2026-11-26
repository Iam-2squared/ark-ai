# Run1109 — Observation fixture ingress regression rebase

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent HEAD: `62047e185d4f8b8fef9a94b3f6441ff1b42c307d`.
- Reapplied from Draft PR #249 exact child HEAD: `55cc505f5c6926fb913b7850e3dcb83d8863b014`.
- New child branch: `research/run1109-observation-fixture-guards-rebase`.
- Tests: `tests/test_observation_fixture_metadata_preflight_run1109.py` and `tests/test_observation_fixture_payload_byte_budget_run1109.py`.

## Coverage

- Text, transcript, image and screen fixture payloads exceeding the 4 MiB UTF-8/binary byte budget are rejected before private hashing.
- Exact-budget text and binary fixtures remain digest-only envelopes with no raw payload field.
- Metadata validation rejects non-exact types, invalid UTF-8, NUL/ASCII control and bidi formatting, boolean timestamps and malformed parent digests before hashing.
- Rebound digest entrypoints are rejected before receiving fixture bytes.

The current fixture adapter source and frozen Observation Envelope v1 contract are unchanged. All values are synthetic and in-memory; no camera, microphone, screen, filesystem, network, notification or ToolBackend is accessed.

## Evidence and limits

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; prior child CI on a different parent/head does not transfer. No local pytest/Ruff PASS is claimed.

This validates local fixture-ingress bounds and hash ordering only. It does not authenticate sources, establish consent, prove capture provenance, trusted time, independent custody, or authorize dispatch. No paid/external compute, Candidate, protected V2 evaluation, credentials, physical hardware, UI/frontend work, frozen-contract change or main merge. PR #8 remains Draft/unmerged. **ARK/JARVIS remains NOT_PASSED.**
