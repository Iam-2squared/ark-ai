# ARK Run1361 — Observation text encoder custody

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `884bd3df8a6966065d0861677bf50eb63db2f9a9`.
- Child branch: `research/run1361-observation-encoder-seal-rebase-20261125`.
- Source/test rebase basis HEAD: `0972bd9fed2bddd29bc95b2302c760980f7240af`.
- Production file: `src/ark/observation_fixture_adapters.py`.
- Regression module: `tests/test_observation_fixture_encoder_custody_run1361.py`.

## Finding and correction

The bounded UTF-8 encoder receives caller-private text before hashing. The fixture adapter already retained and checked import-time identities for its SHA-256 path and private hashing helper, but it looked up `_encode_fixture_text_bounded` through a mutable module binding after metadata preflight. A replacement installed before the call, including during metadata preflight, could therefore observe the raw text.

The adapter now retains the import-time bounded encoder, seals the retained reference vector itself, rejects module-binding or retained-alias replacement before private text access, and invokes only the retained callable. The byte-budget algorithm and its ASCII/multibyte behavior are unchanged.

## Regression coverage

- A preinstalled replacement encoder is rejected without receiving private text.
- A replacement installed during metadata preflight is rejected before it receives private text.
- Replacing both the module binding and retained encoder alias is rejected before the replacement receives private text.
- Replacing the retained encoder reference vector is rejected before private text access.
- The hash sentinel is not called after encoder identity drift.

## Scope and evidence boundary

No Observation Envelope v1 field, constructor, schema, public API, fixture size limit, byte-budget algorithm, lineage format or retention behavior changed. This remains a disconnected synthetic text/transcript fixture path; it does not add camera, microphone, screen, filesystem, network, notification or ToolBackend access. It does not establish source authenticity, consent, trusted time or action permission.

Predecessor PR #532 CI [45535410668](https://github.com/Iam-2squared/ark-ai/actions/runs/45535410668) was GREEN only on its historical base and does not transfer. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS or CI PASS is claimed. No live personal data, paid/external compute, Candidate, protected V2 evaluation, credentials, hardware, destructive operation, frozen-contract change, main merge or UI work occurred. PR #5 and PR #8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
