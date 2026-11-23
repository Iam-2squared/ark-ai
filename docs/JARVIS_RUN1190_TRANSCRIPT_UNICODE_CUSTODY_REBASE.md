# Run1190 — Rebased detached transcript Unicode dependency custody

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `c1b7b3d2dfe38242fcbe3d6d4930c3bbf53e9390`.
- Rebased from Draft PR #370 exact child HEAD `b4724508fcb7d8c51507d9e2922d919c8daa051f`.
- Original child exact-head CI [45178043814](https://github.com/Iam-2squared/ark-ai/actions/runs/45178043814) was GREEN on the prior child head only; it does not transfer.
- New child branch: `research/run1190-transcript-unicode-custody-rebase`.

## Change

The detached transcript binder pins the import-time Unicode module, NFC normalizer and category classifier; checks exact dependency identity before caller text is processed and between normalization, category scanning and UTF-8 encoding; and preserves Cc/Cf/Cs rejection, NFC, segment/total byte limits, frame bounds and denial-only output.

## Regression coverage

Synthetic text and metadata only. U+0600, U+FFF9 and U+E0001 are rejected. Dependency substitution is denied before caller text reaches an unreviewed callback. Existing byte budgets, frame/segment bounds, denial-only semantics and frozen contracts are preserved.

## Validation boundary

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff result is claimed. This is an in-process Unicode dependency-integrity guard, not a Python sandbox, acoustic detection, speaker authentication, consent, command authorization or Tool dispatch. No audio is opened and no ASR is run.

No paid/external compute, paid APIs/services, Candidate generation/promotion, protected V2 evaluation, credentials, physical hardware, destructive operation, frozen-contract change, UI/frontend work or main merge. PR #5 and #8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
