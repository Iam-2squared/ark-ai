# ARK Run1336 — Observation UTF-8 chunk-budget regression

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `2af77814dd01f0959d99a86ddcf9387d94e8053c`.
- Rebased fixture adapter context: `src/ark/observation_fixture_adapters.py`.
- Existing test: `tests/test_observation_fixture_utf8_preallocation_run1152.py`.
- New child branch: `research/run1336-observation-utf8-chunk-boundary-20261125`.

## Finding and correction

The earlier large-multibyte test passed an 8-byte budget for 100,000 codepoints. The encoder's inexpensive `len(content) > max_bytes` check therefore returned before the 16K-codepoint chunk loop, so the test did not exercise cumulative UTF-8 byte accounting.

The revised case makes codepoint count fit the byte budget while four-byte UTF-8 encoding exceeds it. Additional cases exercise an exact accepted budget across a chunk boundary and rejection one byte below that budget.

No production source, fixture limit, hashing behavior, Observation Envelope v1 contract, public API, or real capture path changes.

## Evidence boundary

Synthetic in-memory strings only. No camera, microphone, screen, filesystem, network, live observation, notification, ToolBackend, paid service, Candidate, protected V2 evaluation, credentials, hardware, destructive operation, UI work or main merge. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no PASS is claimed before that run completes.