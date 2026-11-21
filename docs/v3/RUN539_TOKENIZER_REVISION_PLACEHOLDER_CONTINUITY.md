# Run539 — passive tokenizer revision placeholder continuity

**Draft / UNAPPROVED / NOT_PASSED.** This is a disconnected, free-only
syntactic inventory correction on PR #5. It does not supply immutable Hub
revisions, model/tokenizer file hashes, actual human review, license clearance,
GPU/device metadata, billing evidence, consent or training authority.

## Scope and basis

- Initial read basis: PR #5 HEAD
  `153f0d0a2385cd15822d405e3d36904b4579e7b2`.
- Source change `abf2d37b68a0898506ac707ef6f2d2a6abdc13cc`:
  `src/ark/learning/offline_readiness_inventory.py`.
- Regression tests `9dedc6ef280f6106695cb23cd53a316a3c8453af`:
  `tests/v3/test_offline_readiness_tokenizer_alias_run539.py`.
- No frozen `docs/v3/CONTRACT.md` or Experiment 001 template
  changes; original train/validation, Q4_K_M, LoRA and evaluation gates remain.

## Observed defect and correction

The passive unresolved inventory enumerated tokenizer material/hash paths
separately, and added `tokenizer.revision` only when its declared
`SAME_AS_BASE` alias pointed to the exact `UNRESOLVED` base revision.
A base marked `USER_APPROVAL_REQUIRED` remained unresolved, but its
tokenizer alias disappeared from the inventory. A tokenizer revision directly
set to `UNRESOLVED` or `USER_APPROVAL_REQUIRED` was likewise omitted.

The new check counts `tokenizer.revision` whenever its own literal
revision is a recognized placeholder, or it is `SAME_AS_BASE` while the base
revision has either placeholder. The frozen template still has **26**
syntactically unresolved positions. A concrete-looking 40-character revision
is a string, **not** an authenticated model identity. This change does not
alter the shared `_SECTIONS` path contract or authorized execution rules.

**Six new parametrized pytest cases** cover both pending base-marker variants,
both explicit tokenizer markers, a syntactically filled base alias, and an
explicit tokenizer revision over unresolved base. The tests also bind the
canonical JSON SHA-256 and assert that no external compute, Candidate,
protected evaluation or promotion permission is returned.

## CI and hard stops

The exact source+test HEAD `9dedc6ef280f6106695cb23cd53a316a3c8453af`
has **6/6 GREEN** in
[GitHub Actions run 41348330565](https://github.com/Iam-2squared/ark-ai/actions/runs/41348330565):
Ubuntu/Windows Python 3.11, 3.12 and 3.13 all succeeded.
This does not certify the later documentation HEAD or a standalone local
pytest/Ruff run.

No external GPU, paid compute/API, model fetch, actual preflight/training,
Candidate adapter/weight production, protected V2 opening, promotion, frozen
contract changes or main merge. PR #5 remains Draft. Continue only free,
disconnected identity/path/reproducibility audits while actual approvals and
materialized byte evidence remain unresolved.
