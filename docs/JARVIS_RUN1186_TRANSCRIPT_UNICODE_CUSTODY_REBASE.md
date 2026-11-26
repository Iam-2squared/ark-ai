# Run1186 — Rebased transcript Unicode dependency custody

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent HEAD: `1513277445b4308c4712f4a07f16dc13e806819e`.
- Rebased from Draft PR #365 exact child HEAD `41aa9823ce4f2fcf413f192ff2c013b40e1abffd`.
- Prior exact-head CI [45167579843](https://github.com/Iam-2squared/ark-ai/actions/runs/45167579843) was GREEN 6/6 on the original child head only; it does not transfer to this rebase.
- New child branch: `research/run1186-transcript-unicode-custody-rebase`.

## Finding and change

The detached transcript binder pins the import-time Unicode module, NFC normalizer and category classifier; checks exact dependency identity before caller text is processed and between normalization, category scanning and UTF-8 encoding; and preserves Cc/Cf/Cs rejection, NFC, segment/total byte limits, frame bounds and denial-only output.

## Regression coverage

Synthetic text and metadata only. Existing byte budgets, frame/segment bounds, denial-only semantics and frozen contracts are preserved. Dependency substitution is rejected before caller text reaches an unreviewed callback.

## Validation boundary

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff result is claimed. This is an in-process Unicode dependency-integrity guard, not a Python sandbox, acoustic detection, speaker authentication, consent, command authorization or Tool dispatch.

No audio is opened, no ASR is run, and no speaker identity, consent, external disclosure or Tool permission is inferred.

No paid/external compute, paid APIs/services, Candidate generation/promotion, protected V2 evaluation, credentials, physical hardware, destructive operation, frozen-contract change, UI/frontend work or main merge. PR #5 and #8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
