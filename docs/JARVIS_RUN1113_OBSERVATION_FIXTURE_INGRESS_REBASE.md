# ARK Run1113 — rebase Observation fixture ingress regressions

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent HEAD: `4f9e44532cc25dfe57059021519717441399155b`.
- Rebased child branch: `research/run1113-observation-fixture-guards-rebase`.
- Prior child PR #271 branch: `research/run1111-observation-fixture-guards-rebase`, exact head `336ad2aedbdbf6741996bc717f3c59780bc513ad`.
- Prior exact-head CI: [45019523789](https://github.com/Iam-2squared/ark-ai/actions/runs/45019523789), GREEN on the prior child head only; it does not transfer to this rebase.

## Coverage

- Text, transcript, image and screen fixture payloads exceeding the 4 MiB UTF-8/binary byte budget are rejected before private hashing.
- Exact-budget text and binary fixtures remain digest-only envelopes with no raw payload field.
- Metadata validation rejects non-exact types, invalid UTF-8, NUL/ASCII control and bidi formatting, boolean timestamps and malformed parent digests before hashing.
- Rebound digest entrypoints are rejected before receiving fixture bytes.

The production fixture adapter source and frozen Observation Envelope v1 contract are unchanged. All values are synthetic and in-memory; no camera, microphone, screen, filesystem, network, notification or ToolBackend is accessed.

## Evidence and limits

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; prior child CI on a different parent/head does not transfer. No local pytest/Ruff PASS is claimed. This validates local fixture-ingress bounds and hash ordering only. It does not authenticate sources, establish consent, prove capture provenance, trusted time, independent custody or authorize dispatch.

No paid/external compute, Candidate, protected V2 evaluation, credentials, physical hardware, UI/frontend work, frozen-contract change or main merge occurred. PR #5 and PR #8 remain Draft/unmerged. **ARK/JARVIS remains NOT_PASSED.**
