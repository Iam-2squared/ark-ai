# JARVIS Run1250 — Personal Context final-veto regression rebased

## Exact basis

- Repository: `Iam-2squared/ark-ai`.
- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `99654a0ecc75fe53de7f38d92db42095391df6e4`.
- Test-only rebase from Draft PR #431, source child HEAD `a5ad500bc3f5ea8d8a5cd2e0c8672b240407ebd4`.
- The final local revocation recheck is already present in the parent implementation; this child changes no Personal Context source, Memory source/schema, frozen contract or public API.

## Coverage

A synthetic Memory row and separate synthetic revocation ledger are created. The test injects a revocation during final retained-history review, after the prior history read, and requires the local projection to reject before returning. It verifies exactly one revocation row and confirms the persisted ledger excludes owner identity and raw synthetic private content.

## Evidence boundary

The source child CI [45329015031](https://github.com/Iam-2squared/ark-ai/actions/runs/45329015031) completed successfully on the older parent. That result does not certify this rebased child; fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required.

This final local veto narrows one race only. It is not an atomic downstream-use lease, authenticated consent, or proof of physical erasure. Synthetic disposable local SQLite only; no live personal data or external service.

No paid/external compute, Candidate generation/promotion, protected V2 evaluation, credentials, hardware, destructive action, frozen-contract change, UI/frontend work or main merge. PR #5/#8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
