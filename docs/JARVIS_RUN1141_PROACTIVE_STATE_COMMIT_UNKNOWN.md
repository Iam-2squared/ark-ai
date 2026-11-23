# Run1141 — proactive state ambiguous COMMIT outcome

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Parent work-basis HEAD: `e7b49bfb257b0adaf07b3e7b2e52e7f4ca2bf6e8` (after the exact-head-GREEN Personal Context SQLite factory rebase was integrated).
- Child branch: `research/run1141-proactive-state-commit-unknown`.
- Test: `tests/test_proactive_state_commit_unknown_run1141.py`.

## Coverage

The subprocess regression injects a lost SQLite COMMIT acknowledgement at the proactive eligibility ledger's write boundary, testing both possible outcomes:

1. The underlying transaction commits durably and the acknowledgement is lost.
2. The underlying transaction rolls back and the acknowledgement is lost.

In both cases the public `evaluate` call raises, and the injected boundary records exactly one COMMIT attempt. A cold ledger then reads the persisted outcome without automatic retry. If the transaction was durable, a stale genesis revision is rejected and the preview remains a single row. If it rolled back, the cold read reports no row.

The subprocess installs its stable SQLite factory before importing ARK, then arms only the exact read/write URI used by the tested evaluation. The fixture uses disposable local SQLite and synthetic digests.

## Evidence boundary

This is a local state-ledger COMMIT-ambiguity regression only. It does not prove fsync/power-loss durability, independent storage custody, trusted time, authenticated observation provenance, consent, timer/notification permission, external dispatch, or exactly-once effects. The proactive state schema, policy, CAS algorithm, and denial-only authority flags are unchanged. No real scheduler or notification service is invoked.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required before any PASS claim. No local pytest/Ruff result is claimed. PR #8 and PR #5 remain Draft/unmerged; PR #9 remains untouched; ARK/JARVIS remains NOT_PASSED.
