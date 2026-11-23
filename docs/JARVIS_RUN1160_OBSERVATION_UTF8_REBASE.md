# Run1160 — Observation fixture UTF-8 allocation rebase

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent HEAD at child creation: `aa466abdf3de9abc9d1560e614952596c7cc8b19`.
- Rebased the bounded text-fixture encoder and regression from Draft PR #341 exact child HEAD `d5e7ea28072ea1fc5cdd615c364a4d45b866b91e`.
- Source exact-head CI [45120086283](https://github.com/Iam-2squared/ark-ai/actions/runs/45120086283) was GREEN on the source head only; it does not transfer to this rebase.
- New branch: `research/run1160-observation-utf8-rebase`.

## Change

The disconnected text fixture adapter previously encoded the full payload before enforcing its UTF-8 byte budget. This package adds a strict bounded encoder with an ASCII fast path and 16K-codepoint non-ASCII chunks, stopping when cumulative bytes exceed the fixed 4 MiB limit. Tests cover ASCII and multibyte exact boundaries, early rejection, invalid surrogate handling, and denial before private hashing.

The binary fixture adapter, digest-only envelope, and frozen Observation Envelope v1 contract remain unchanged. The adapter still accepts only caller-supplied in-memory fixtures; it does not acquire camera, microphone, screen, file, or network data.

## Validation boundary

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. This is local allocation/ingress hardening, not source authenticity, consent, provenance, real capture, or execution-authority evidence. No paid/external compute, Candidate, protected V2 evaluation, credentials, hardware, UI/frontend work, destructive operation, or main merge. PR #5 and #8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
