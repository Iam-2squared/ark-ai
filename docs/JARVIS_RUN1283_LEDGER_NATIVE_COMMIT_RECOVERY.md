# ARK Run1283 — Durable-ledger native-COMMIT crash regressions

## Exact basis

- Repository: `Iam-2squared/ark-ai`.
- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `ddc4a574437361059552615ceb44936a628555dc`.
- Child branch: `research/run1283-ledger-native-commit-recovery-rebase`.
- Test-only rebase of the existing Memory, Personal Context replay and proactive-state hard-exit regressions (predecessor Draft PRs #456, #458 and #457).
- No production source, schema, DDL, public API or frozen contract is changed.

## Regression coverage

- **Memory expiry purge:** a spawned child exits immediately after the native SQLite transaction commit, before `purge_expired` returns. Cold recovery checks the target row is gone, a live row and foreign namespace are preserved, the `expire` event is present exactly once, and a retry adds no duplicate event.
- **Personal Context replay:** a spawned child exits after native SQLite COMMIT but before `reserve` returns its receipt. Cold recovery checks one hash-only reservation, retained-prefix continuity, absence of raw fixture text in the database/sidecars, and duplicate-request denial.
- **Proactive state:** a spawned child exits after native SQLite COMMIT but before `evaluate` returns. Cold recovery checks the single eligible preview, exact state fields, false-only authority flags, privacy-minimized persistence, stale-CAS rejection and a subsequent unchanged CAS without a second preview.

## Evidence boundary

These are synthetic local SQLite process-exit tests after a successful native COMMIT. They do **not** prove fsync or power-loss durability, trusted time, authenticated consent, revocation freshness, notification authorization, external dispatch, cross-store atomicity or exactly-once external effects. No live personal data or real backend is used.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no PASS is claimed before that run completes. No paid/external compute, Candidate generation/promotion, protected V2 evaluation, credentials, hardware, destructive action, UI/frontend work, frozen-contract change or main merge is performed. PR #5/#8/#9 remain under their existing gates; ARK/JARVIS remains NOT_PASSED.
