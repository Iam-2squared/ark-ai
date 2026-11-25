# Run1410 — V3 dataset admission authority epoch

Status: isolated free-only guard hardening for gated Draft PR #5. No V3 PASS is claimed.

## Exact basis

- Parent: Draft PR #5, branch `research/v3-learning-evaluation`.
- Exact parent work-basis HEAD: `2c3501930baff61f04b25e7e02c00b0241a426e7`.
- Child branch: `research/run1410-v3-dataset-admission-epoch-20261125`.
- Scope: `src/ark/learning/dataset.py` and one synthetic regression file.

## Finding

The dataset admission boundary compared `_ORIGINAL_LEARNING_CANDIDATE_TYPE` with its paired validator alias, and did the same for `ContaminationGuard`. A coordinated rebinding of each private type alias and its validator alias to a replacement dataclass plus no-op validator remained self-consistent under those pairwise checks. The replacement candidate and guard could therefore reach the deterministic dataset builder without the originally defined admission and contamination-review implementations.

## Change

- Capture the public `LearningCandidate` and `ContaminationGuard` names, their private original type aliases, and the exact validator/reason functions in one immutable import-time tuple.
- Retain that tuple in the admission checker’s default argument.
- Verify tuple identity, public-name identity, private-alias identity and class-namespace method identity before dataset candidate inspection or policy callbacks.
- Preserve the existing candidate fields, validation criteria, contamination rules, sorting, duplicate handling, rejection format, canonical bytes and dataset schema.

## Regression coverage

- A coordinated replacement of both dataclass types and both validator aliases is rejected before either replacement callback runs.
- An equal-valued but distinct replacement of the retained admission-epoch tuple is rejected.
- Fixtures are synthetic; no real dataset or personal data is used.

## Evidence boundary and blocker

This is local admission-implementation identity hardening only. It does not prove source rights, independent human approval, semantic contamination absence, provenance completeness, training success, Candidate weights, V2 evaluation or promotion. Frozen Contract 1, dataset schema and experiment parameters are unchanged.

A historical PR #5 parent-head run `45589076269` **FAIL**ed before pytest at `ruff check .` on three import-order violations; its job logs show pytest skipped. The child exact-head run `45627825798` for `73f93c46cda8832a82ed5a20579324a11cec64ff` is **GREEN, 6/6** (Windows/Linux × Python 3.11–3.13). The child result is the applicable validation evidence for this package; the older parent run is retained only as historical context.

No paid/external compute, paid service, Candidate generation/promotion, protected V2 evaluation, credentials, account connection, hardware, destructive action, frozen-contract change, main write/merge or UI/frontend work occurred. PR #5 remains Draft/unmerged. PR #8/#9 remain Draft/unmerged; UI/frontend work remains paused.

Exact-head CI evidence: source/test HEAD `73f93c46cda8832a82ed5a20579324a11cec64ff` run `45627825798` GREEN 6/6; evidence-only HEAD `93b8b61281606bbdadf3d0f33dffdeace64aa400` run `45628627183` GREEN 6/6. This follow-up is documentation-only; its resulting HEAD requires its own exact-head CI.
