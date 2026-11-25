# ARK Run1285 — Personal Context final revocation veto

## Exact basis

- Repository: `Iam-2squared/ark-ai`.
- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `d71744cfac4de02c61df6e47102f22e876d4d0c6` (after Run1300 guard-custody integration).
- Original child: `research/run1294-context-final-veto-rebase-20261124`.
- Rebased child: `research/run1304-context-final-veto-rebase-20261125`.
- Test-only rebase of the final-history revocation-veto regression previously carried by Draft PR #459.
- Current revocation continuity implementation was inspected before the test was copied.

## Regression coverage

The synthetic fixture appends a revocation during the final retained-history continuity review, after the earlier snapshot/history read. The Personal Context projection must fail closed before return. The test also checks that the revocation ledger contains one digest-only row and does not persist the raw owner identifier or synthetic private content.

## Evidence boundary

This narrows a local revocation race in a disconnected review flow. It is **not** an atomic downstream-use lease, authenticated consent, trusted-time proof, independent custody, a physical erasure guarantee, or authorization to disclose/dispatch context. Memory and revocation remain separate local stores. Synthetic data only.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no PASS is claimed before that run completes. No production source, schema, public API, frozen privacy contract, downstream-use lease or authorization semantics are changed. No paid/external compute, Candidate, protected V2 evaluation, credentials, hardware, destructive action, UI/frontend work or main merge. PR #5/#8/#9 remain under their existing gates; ARK/JARVIS remains NOT_PASSED.
