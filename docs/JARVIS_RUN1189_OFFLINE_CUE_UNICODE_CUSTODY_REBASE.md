# Run1189 — Rebased offline transcript cue Unicode dependency custody

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `c1b7b3d2dfe38242fcbe3d6d4930c3bbf53e9390`.
- Rebased from Draft PR #371 exact child HEAD `6378f2fb716d6160ec4fdb5f22620db957cda1c3`.
- Original child exact-head CI [45178160046](https://github.com/Iam-2squared/ark-ai/actions/runs/45178160046) was GREEN on the prior child head only; it does not transfer to this rebase.
- New child branch: `research/run1189-offline-cue-unicode-custody-rebase`.

## Change

The disconnected transcript cue parser pins the import-time Unicode module, exact category function and NFKC normalizer; checks them before and after text scanning/normalization; and preserves existing control/invisible-character rejection, NFKC case-folding, cue-boundary rules and byte budgets.

## Regression coverage

Synthetic transcript/cue text only. U+0600, U+FFF9 and U+E0001 are rejected; ordinary text remains supported; module/normalizer/category substitutions are denied before unreviewed callbacks receive caller text.

## Validation boundary

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff result is claimed. This is text-only fixture parsing, not acoustic wake-word detection, speaker authentication, consent, command authorization or Tool dispatch. Unicode dependency pinning is an in-process integrity guard, not a Python sandbox or independent runtime attestation.

No paid/external compute, paid APIs/services, Candidate generation/promotion, protected V2 evaluation, credentials, physical hardware, destructive operation, frozen-contract change, UI/frontend work or main merge. PR #5 and #8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
