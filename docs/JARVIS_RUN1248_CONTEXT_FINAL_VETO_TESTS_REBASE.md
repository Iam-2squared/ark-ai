# JARVIS Run1248 — Personal Context final-veto regression rebased

## Exact basis

- Repository: `Iam-2squared/ark-ai`.
- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `126bf11c2070c261de86b7a94ebdd0e67f52be6a`.
- This package carries the synthetic final-veto regression from older Draft PR #10 onto the current foundation head.
- The final local revocation recheck is already present in `src/ark/personal_context_revocation_review.py` (observed blob `2d44543e7b48b03a04d3e08a0f6b5f836c3d3efb`); this child adds tests only.
- Previous PR #10 CI [44500056645](https://github.com/Iam-2squared/ark-ai/actions/runs/44500056645) was GREEN 6/6 on its older child head. That result does not certify this rebased child; fresh exact-head CI is required.

## Coverage

A synthetic Memory row and separate synthetic revocation ledger are created. The test injects a revocation during the final retained-history review, after the prior history read, and requires the local projection function to reject the result before returning it. It verifies exactly one revocation row and confirms the persisted ledger does not contain the owner ID or raw synthetic private content.

## Scope and evidence boundary

Test-only. No Personal Context source, Memory source/schema, frozen contract or public API changes. The extra final veto narrows a local race only; it is not an atomic lease for later model/tool/export consumption, authenticated consent, or proof of physical erasure. Synthetic disposable local SQLite only; no live personal data or external service.

No paid/external compute, Candidate generation/promotion, protected V2 evaluation, credentials, hardware, UI/frontend work, destructive action, frozen-contract change or main merge. PR #5/#8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
