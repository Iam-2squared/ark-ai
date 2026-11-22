# Run1110 — Observation fixture ingress regression rebase

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent HEAD: `d08cf2bdbc7cdd3142b4ab3945cacf39d29ca607`.
- Reapplied from Draft PR #262 exact child HEAD: `6e114402885d73082b4e126de7c99b2cd58645eb`.
- New child branch: `research/run1110-observation-fixture-guards-rebase`.
- Tests: `tests/test_observation_fixture_metadata_preflight_run1110.py` and `tests/test_observation_fixture_payload_byte_budget_run1110.py`.

## Coverage

- Text, transcript, image and screen fixture payloads exceeding the 4 MiB UTF-8/binary byte budget are rejected before private hashing.
- Exact-budget text and binary fixtures remain digest-only envelopes with no raw payload field.
- Metadata validation rejects non-exact types, invalid UTF-8, NUL/ASCII control and bidi formatting, boolean timestamps and malformed parent digests before hashing.
- Rebound digest entrypoints are rejected before receiving fixture bytes.

The current fixture adapter source and frozen Observation Envelope v1 contract are unchanged. All values are synthetic and in-memory; no camera, microphone, screen, filesystem, network, notification or ToolBackend is accessed.

## Evidence and limits

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; prior child CI on a different parent/head does not transfer. No local pytest/Ruff PASS is claimed.

This validates local fixture-ingress bounds and hash ordering only. It does not authenticate sources, establish consent, prove capture provenance, trusted time, independent custody, or authorize dispatch. No paid/external compute, Candidate, protected V2 evaluation, credentials, physical hardware, UI/frontend work, frozen-contract change or main merge. PR #8 remains Draft/unmerged. **ARK/JARVIS remains NOT_PASSED.**


Rebased child CI is required on this exact branch head. The predecessor PR #262 exact-head run #7061 / 45010743101 is GREEN on the previous base only and is not transferred.
