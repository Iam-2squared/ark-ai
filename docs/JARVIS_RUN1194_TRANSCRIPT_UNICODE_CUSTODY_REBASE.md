# Run1194 — Detached transcript Unicode dependency custody rebase

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent HEAD at branch creation: `2df6b261554428cd01871f2723ce87c4dd05e4b4`.
- Reconciled source: Draft PR #374 exact child HEAD `57083b111aafc8829ef15f37d886ae8ade110f32`.
- Original source PR #370 exact child HEAD: `b4724508fcb7d8c51507d9e2922d919c8daa051f`.
- New child branch: `research/run1194-transcript-unicode-custody-rebase`.

## Change

The detached transcript binder pins the import-time `unicodedata` module, NFC normalizer and category classifier; checks exact dependency identity before caller text is processed and between normalization, category scanning and UTF-8 encoding; and preserves Cc/Cf/Cs rejection, NFC, segment/total byte limits, frame bounds and denial-only output.

## Regression coverage

Synthetic text/metadata only: U+0600/U+FFF9/U+E0001 rejection and module/normalizer/category substitution denial before callback use. Existing byte budgets, frame/segment bounds and denial-only semantics remain.

## Limits

No audio is opened, no ASR is run, and no speaker identity, consent, external disclosure or Tool permission is inferred. Unicode dependency pinning is an in-process integrity guard, not a Python sandbox or independent runtime attestation.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed. No paid/external compute, paid APIs/services, Candidate, protected V2 evaluation, credentials, physical hardware, destructive operation, frozen-contract change, UI/frontend work or main merge. PR #5 and #8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
