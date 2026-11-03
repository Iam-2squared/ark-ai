# Run542 — Passive unapproved V3 identity label shape review

**Draft / NOT_PASSED / no execution authorization.** This is a syntax-only
improvement to an existing **offline** review of an **unapproved** experiment
snapshot, not verification of file bytes, repository commit identity, human
decisions, provider billing controls, model loading, training or evaluation.

- Source: `668c973f086dc93e273dd2946408ce91fb444288`.
- Tests: `08e6ffd86473a46e1cb1a9b65ca86afbe75f173a`.
- Existing `_plausible_shape` default label branch in
  `src/ark/learning/offline_snapshot_shape_review.py` now flags leading/
  trailing whitespace and nonprintable codepoints (such as embedded NUL,
  newline, carriage return, DEL and zero-width formatting characters).
  The strict 40-hex and 64-hex pin checks and the frozen V3 contract remain
  unchanged. Literal placeholder inventory remains independent of syntax.
- **11 authored parameter-expanded test cases** cover malformed and printable
  environment/hardware labels, a revision field, and non-authorizing outputs.
- Exact source+test HEAD `08e6ffd86473a46e1cb1a9b65ca86afbe75f173a`:
  GitHub Actions CI [41364207690](https://github.com/Iam-2squared/ark-ai/actions/runs/41364207690)
  was checked as **6/6 completed successful jobs** before this note.
  Later note/checkpoint commits need separate exact-head CI verification.
- `docs/v3/CONTRACT.md` blob
  `b44f7b0e7e619c225ab662ed9c1fc8deae2b1e23` remains unchanged.

**Unresolved hard gates:** immutable base/tokenizer byte identities and Hub
revisions, exact runtime and hardware pins, licensed/reviewed 120+30 data,
human approval, cost ceiling and provider-side billing controls, explicit
separate preflight/full-training authorization, and protected V2 evaluation
opening. No paid API, external GPU, actual Candidate, promotion, or protected
evaluation is permitted. PR #5 stays Draft/unmerged.
