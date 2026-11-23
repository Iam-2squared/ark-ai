# Run1156 — Observation fixture UTF-8 allocation rebase

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `9b1dbc439ec338e2840d9dc493e724c651617e60`.
- Rebased from Draft PR #337 exact child HEAD: `8ab8e479840d39241bfef72b970427f4af172d33`.
- Source exact-head CI: [45114692863](https://github.com/Iam-2squared/ark-ai/actions/runs/45114692863) GREEN, 6/6 on the source head only; it does not transfer to this rebase.
- New child branch: `research/run1156-observation-utf8-rebase-latest`.
- Source: `src/ark/observation_fixture_adapters.py`.
- Regression tests: `tests/test_observation_fixture_utf8_preallocation_run1152.py`.

## Change

The text fixture adapter previously encoded the complete payload before checking its UTF-8 byte length. A non-ASCII string within the code-point cap can expand to as much as four UTF-8 bytes per code point, so the byte check rejected oversized data only after allocating the complete expanded byte string.

The bounded encoder preserves the 4 MiB budget and strict UTF-8 behavior, uses a direct ASCII path, and encodes non-ASCII text in 16K-codepoint chunks, stopping as soon as cumulative bytes exceed the limit. The binary fixture path and digest-only envelope remain unchanged.

## Validation scope

Synthetic tests cover ASCII/multibyte exact boundaries, early oversize rejection, strict surrogate rejection, and denial before private hashing. No camera, microphone, screen, file, network, notification, ToolBackend, consent, source authentication, or real capture is used.

The public/frozen Observation Envelope v1 contract, schema, and adapter IDs are unchanged. This is local resource-bound hardening, not provenance or execution-authority evidence. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no PASS is claimed until that run completes.

No V1/V2 evidence, PR #5, PR #8, PR #9, UI/frontend work, main branch, paid service, external compute, Candidate, protected evaluation, credential, or physical hardware action is changed or used. ARK/JARVIS remains NOT_PASSED.
