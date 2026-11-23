# Run1187 — Rebased offline transcript cue Unicode dependency custody

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent HEAD: `1513277445b4308c4712f4a07f16dc13e806819e`.
- Rebased from Draft PR #366 exact child HEAD `f98b6d90d52e178df35261ff5d0e8449f575f757`.
- Prior exact-head CI [45167608082](https://github.com/Iam-2squared/ark-ai/actions/runs/45167608082) was GREEN 6/6 on the original child head only; it does not transfer to this rebase.
- New child branch: `research/run1187-offline-cue-unicode-custody-rebase`.

## Finding and change

The disconnected wake-cue parser pins the import-time Unicode module, exact category function and NFKC normalizer; checks them before and after text scanning/normalization; and preserves existing control/invisible-character rejection, NFKC case-folding, cue-boundary rules and byte budgets.

## Regression coverage

Synthetic transcript/cue text only. U+0600, U+FFF9 and U+E0001 are rejected; ordinary text remains supported; module/normalizer/category substitutions are denied before unreviewed callbacks receive caller text.

## Validation boundary

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff result is claimed. This is text-only fixture parsing, not acoustic wake-word detection, speaker authentication, consent, command authorization or Tool dispatch. Unicode dependency pinning is an in-process integrity guard, not a Python sandbox or independent runtime attestation.

No paid/external compute, paid APIs/services, Candidate generation/promotion, protected V2 evaluation, credentials, physical hardware, destructive operation, frozen-contract change, UI/frontend work or main merge. PR #5 and #8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
