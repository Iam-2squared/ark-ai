# ARK Run1353 — Observation text encoder custody

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `8c969bbd2dc83c800b7bad998fd8e480aec941e7`.
- Child branch: `research/run1353-observation-text-encoder-custody-20261125`.
- Implementation and regression head before this evidence note: `7e1faae958ce06bb425454a612df2935200401c8`.
- Production file: `src/ark/observation_fixture_adapters.py`.
- Regression module: `tests/test_observation_fixture_encoder_custody_run1353.py`.

## Finding and correction

The bounded UTF-8 encoder receives caller-private text before hashing. The fixture adapter already retained and checked import-time identities for its SHA-256 path and private hashing helper, but it looked up `_encode_fixture_text_bounded` through a mutable module binding after metadata preflight. A replacement installed before the call, including during metadata preflight, could therefore observe the raw text.

The adapter now retains the import-time bounded encoder, rejects a changed module binding after metadata preflight, and invokes the retained callable. The byte-budget algorithm and its ASCII/multibyte behavior are unchanged.

## Regression coverage

- A preinstalled replacement encoder is rejected without receiving private text.
- A replacement installed during metadata preflight is rejected before it receives private text.
- The hash sentinel is not called after encoder identity drift.

## Scope and evidence boundary

No Observation Envelope v1 field, constructor, schema, public API, fixture size limit, byte-budget algorithm, lineage format or retention behavior changed. This remains a disconnected synthetic text/transcript fixture path; it does not add camera, microphone, screen, filesystem, network, notification or ToolBackend access. It does not establish source authenticity, consent, trusted time or action permission.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS or CI PASS is claimed. No live personal data, paid/external compute, Candidate, protected V2 evaluation, credentials, hardware, destructive operation, frozen-contract change, main merge or UI work occurred. PR #5 and PR #8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
