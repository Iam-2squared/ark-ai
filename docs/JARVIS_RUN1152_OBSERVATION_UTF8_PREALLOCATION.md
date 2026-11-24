# Run1152 — bounded UTF-8 allocation for Observation fixtures

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Parent HEAD at branch creation: `84630edf7847b84fe01e8d6bb97266c60278976a`.
- Child branch: `research/run1152-observation-utf8-preallocation`.
- Source: `src/ark/observation_fixture_adapters.py`.
- Regression tests: `tests/test_observation_fixture_utf8_preallocation_run1152.py`.

## Change

The text fixture adapter previously called `content.encode("utf-8")` before checking the encoded byte length. Its code-point precheck rejects strings longer than the 4 MiB cap, but a shorter non-ASCII string can expand to as much as four UTF-8 bytes per code point. The subsequent byte check prevented hashing an oversized payload but only after allocating the complete expanded byte string.

The new private encoder:

- retains the existing 4 MiB fixture byte budget and strict UTF-8 semantics;
- uses the direct one-byte path for ASCII after checking its code-point lower bound;
- encodes non-ASCII text in 16K-codepoint chunks and stops as soon as cumulative bytes exceed the limit;
- keeps temporary over-budget expansion bounded to one chunk rather than materializing the full expanded payload;
- preserves the existing digest-only envelope and private-hash boundary.

The binary fixture path is unchanged. The public/frozen Observation Envelope v1 contract, schema, and adapter IDs are unchanged.

## Validation scope

New synthetic unit coverage checks ASCII and multibyte exact boundaries, early oversize rejection, invalid-surrogate rejection, and that invalid fixture text never reaches the private hash helper. Existing Run1110 tests continue to cover the adapter's 4 MiB payload boundary.

No camera, microphone, screen, file, network, notification, ToolBackend, consent, source authentication, or real capture is used. This is a local allocation/resource-bound improvement, not a provenance or execution-authority claim. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no PASS is claimed before that run completes.

No frozen contract, V1/V2 evidence, PR #5, PR #8, PR #9, UI/frontend work, main branch, paid service, external compute, Candidate, protected evaluation, credential, or physical hardware action is changed or used. ARK/JARVIS remains NOT_PASSED.
