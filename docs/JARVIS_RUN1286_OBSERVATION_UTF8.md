# ARK Run1286 — Observation fixture UTF-8 allocation regression

## Exact basis

- Repository: `Iam-2squared/ark-ai`.
- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `ddc4a574437361059552615ceb44936a628555dc`.
- Child branch: `research/run1286-observation-fixture-utf8-rebase`.
- Test-only rebase of the bounded Observation text-fixture encoder regression previously developed on source branch `research/run1160-observation-utf8-rebase`.
- Current `src/ark/observation_fixture_adapters.py` was inspected; the bounded encoder and strict UTF-8 rejection path are present.

## Regression coverage

- ASCII and multibyte exact byte-budget boundaries.
- Early rejection of oversized multibyte text without first building a second full-size UTF-8 byte string.
- Strict surrogate rejection.
- Invalid fixture text is rejected before private hashing.

## Evidence boundary

Synthetic in-memory fixture strings only. No camera, microphone, screen, file, network, notification, ToolBackend, consent or real capture is used. The frozen Observation Envelope v1 contract, schema and adapter IDs remain unchanged. This is local allocation/ingress hardening, not source authenticity, provenance, consent or execution authority.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no PASS is claimed before that run completes. No paid/external compute, Candidate, protected V2 evaluation, credentials, hardware, destructive action, UI/frontend work, frozen-contract change or main merge. PR #5/#8/#9 remain under their existing gates; ARK/JARVIS remains NOT_PASSED.
