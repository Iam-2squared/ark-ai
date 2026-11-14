# ARK JARVIS — Run534 offline schedule restart/cursor bridge

**Status: Draft / disconnected / reversible / NOT_PASSED.** 2026-11-02 JST.
Only synthetic local schedule and SQLite fixtures. This record is not
authorization evidence, trusted time, real notification, Tool execution or
automatic repeat permission.

## Work basis and exact source history

- Initial PR #8 HEAD before Run534: `1b2a7c05211cfab59a6bc28e0620dfaa41e559a9`.
- Independent source `src/ark/offline_schedule_resume_review.py` at
  `53608216713c474517324d977ad8898a1cf8c995`.
- New test `tests/test_offline_schedule_resume_run534.py` at
  `4fc7d4f6cfbd03cf77a74b879d3d5904e7d23d5b`
  (16 authored parametrized pytest cases).
- Source-only CI [41328654709](https://github.com/Iam-2squared/ark-ai/actions/runs/41328654709)
  **FAILED** Ruff I001 due to an import-order-only mistake. No semantics
  were weakened; the correction is commit
  `77644477b909d37f0ffd29d1e8c8624d5fa903e7`.
- Corrected source/test CI [41328788511](https://github.com/Iam-2squared/ark-ai/actions/runs/41328788511):
  **IN PROGRESS** at the moment this note was constructed. Do not claim
  all 6/6 GREEN until individually verified.
- The authored cases are not standalone local pytest PASS evidence.

## Contract

The new `review_offline_schedule_resume` is a **read-only join** of two
separately developed, disconnected fixtures. The supplied
`DisconnectedSchedulePolicy` must exactly match the persisted
`QuarantinePolicy`; a caller-held `QuarantineWitness` must match the
durable chain; the caller's `DisconnectedScheduleCursor.next_index` must
equal the quarantine count. The previous occurrence ID must equal the
deterministic last quarantined slot (or be absent at genesis).

A single timestamp supplied by the caller classifies **only the next**
hypothetical occurrence as `NOT_DUE`, `DUE_UNVERIFIED`,
`EXPIRED_QUARANTINE` or `EXHAUSTED`. At no point does this API perform
a quarantine write, advance the cursor or verify that any real action
happened. It compares SQLite inspect witnesses before and after the
preview and again after denied-authority callbacks. Its result contains
only count, SHA, next synthetic occurrence, state and a deterministic
review hash.

Adversarial cases: due/grace timing boundary, restart from SQLite
quarantine history, stale cursor and previous-slot mismatch, wrong
policy/retained hash, exact clock type, reentrant cursor modification,
drift between SQLite reads, and mutation from a false-valued authority
property. An external database rewrite could evade comparison without
independently trusted custody. An ordinary caller clock is **not**
trusted-clock authority.

## Hard limits / integration

The returned review expressly denies trusted clock, consent, notification,
Tool execution and automatic replay. No task scheduler, OS timer, real
microphone, network, paid GPU/API, training, protected V2 evaluation,
Candidate, promotion, irreversible operation, main merge or frozen
contract was changed. PR #5/#8 remain Draft/unmerged.

Next dependency: retain independent, authenticatable occurrence custody
and link exact-type PermissionGate + trusted clock audit-before-action
before considering ANY production-side proactive effects. A corrupted
or UNKNOWN WRITE remains manual-only and cannot be inferred from this
fixture.
