# V3 Run1226 — exact review-queue input admission

## Exact basis

- Repository: `Iam-2squared/ark-ai`.
- Parent: Draft PR #387, branch `research/run1203-v3-dataset-duplicate-key-guard`.
- Exact parent work-basis HEAD: `23eca5ec3cf853fd20af605c9c1ffcef220bfd59`.
- New child branch: `research/run1226-review-queue-exact-inputs`.
- This package is isolated from PR #5 and PR #8. It does not modify either parent branch.

## Finding and repair

The V3 human-review queue helpers are local Python API boundaries in addition to their JSON-fed CLI path. Before this change, `ReviewPair.validate` accepted string subclasses and numeric subclasses, and the sampling helpers accepted list subclasses and boolean values for numeric policy parameters. Those carriers can execute caller-defined methods during validation or be mistaken for ordinary numeric policy values.

The review queue now requires exact `ReviewPair` and `LearningCandidate` instances, exact built-in lists, exact strings, and exact built-in integer/float policy values. Similarity scores and sampling fractions are converted only after exact-type admission and must be finite and within their existing bounds. The sampling minimum must be an exact positive integer.

The existing SHA-ordered sampling, flagged-pair coverage, queue fields, dataset schema, review requirements, frozen experiment recipe and authorization gates are unchanged.

## Regression coverage

Synthetic tests cover:

- string and numeric subclasses whose overridden methods must not run;
- ReviewPair and LearningCandidate subclasses with hostile attribute access;
- list subclasses with hostile iteration;
- boolean, non-finite, zero and out-of-range sampling policy values;
- an ordinary exact-type queue to verify existing review and sampling semantics.

## Evidence and hard stops

This is local input-integrity hardening only. It does not supply human-review decisions, approve dataset provenance, authorize real preflight/training, load weights, generate a Candidate, open protected V2 evaluation, promote anything, or change frozen Contract 1.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed. No paid/external compute, Candidate adapter/weight generation or promotion, protected V2 evaluation, credentials, new account connection, hardware action, destructive operation, frozen-contract change, UI/frontend work or main merge. PR #5 remains Draft/unmerged; PR #8 and PR #9 remain untouched. ARK/JARVIS remains NOT_PASSED.
