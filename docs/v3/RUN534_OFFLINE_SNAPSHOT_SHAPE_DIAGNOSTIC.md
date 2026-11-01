# Run534 — Passive V3 snapshot shape and dependent alias review

**Status: Draft / unapproved / NOT_PASSED.** Date: 2026-11-02 JST.
No execution, model access, credentials, remote compute, Candidate generation,
payment, protected V2 evaluation, promotion or contract change.

## Exact branch evidence

- PR #5 [Draft](https://github.com/Iam-2squared/ark-ai/pull/5),
  initial HEAD `96bb31ef2a5e0604058b5a8ea7f4816cf27f8c3c`.
- Source `src/ark/learning/offline_snapshot_shape_review.py`
  at `7a02d7db8d1560d8033b1541ccab7b00ed8e6a11`.
- Focused test `tests/v3/test_offline_snapshot_shape_review_run534.py`
  at `9ebef9efe616e65520aebc5e23fffb2f8a512efb`.
- Ruff I001 **import-only** repair at
  `86a51798d623b4b7a15dd73966f0b8d5103259c7`;
  the earlier source/test CI ran FAIL, not GREEN.
- The corrected test arranges a non-placeholder synthetic SHA so a
  reentrant callback is actually reached; test-only correction at
  `aebc9b13a8d2e8beba62b1fe08e23344a51931ec`.
- Exact source + test [CI run 41328539860](https://github.com/Iam-2squared/ark-ai/actions/runs/41328539860):
  **all 6/6 jobs GREEN** (Ubuntu/Windows, Python 3.11/3.12/3.13).
  25 newly authored parametrized pytest cases; standalone local pytest
  was not executed.

## Motivation and behavior

The prior passive inventory intentionally counts literal unresolved template
positions. It is *not* an execution-validity predicate. Replacing every
placeholder with a synthetic but malformed string could make the literal
unresolved count zero. Run534 adds a **separate, content-free shape report**:

- Reuses the original unapproved/false-authorization inventory and its
  canonical snapshot digest, with a pinned JSON-tree epoch.
- Distinguishes `unresolved_paths` from `invalid_shape_paths` using
  exact-format SHA-256, 40-hex revision, bounded numeric-budget/VRAM and
  nonempty environment/identity carrier checks. Reports only field names.
- Accounts for `tokenizer.revision=SAME_AS_BASE`: when the base revision
  remains `UNRESOLVED` or `USER_APPROVAL_REQUIRED`, the tokenizer revision
  remains unresolved; when the base is malformed, the alias is invalid.
- Enforces exact `False` authorization on the input and on six separate
  output authority properties. A final false getter cannot mutate the result
  or an earlier denied descriptor without rejection.
- No network, filesystem, torch/transformers/PEFT import, GPU, training,
  approval, file hash lookup, cost estimate or real-world action.

A 40-hex commit string or 64-hex digest **does not establish** that the
referenced blob or dataset exists, was reviewed, or matches approved bytes.
Even an inventory with zero missing fields and zero shape warnings remains
**unverified and unauthorized**. This review is a pre-compute diagnostic,
not the official authoritative runtime gate.

## Remaining blocked prerequisites

Immutable actual Hugging Face base/tokenizer bytes and revision,
human-approved dataset/provenance/contamination decisions, exact code/export
and runtime identities, approved hardware/billing caps and explicit spend
authorization remain unresolved. Protected V2 final evaluation is gated
separately. Frozen Contract 1, Experiment 001 and V1/V2 evidence are
untouched. PR #5 stays Draft/unmerged; no main merge or Candidate.
