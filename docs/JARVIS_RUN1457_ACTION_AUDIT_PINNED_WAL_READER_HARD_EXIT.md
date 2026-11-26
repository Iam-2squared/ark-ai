# Run1457 — ActionAudit native COMMIT with a surviving WAL reader

**Parent:** Draft PR #638, branch `research/run1450-planner-audit-native-commit-hard-exit-20261126`.
**Exact parent work-basis HEAD:** `4f57e4c282cd739d7bf2453177e1430f7e4c12d4`.
**Child:** `research/run1457-action-audit-pinned-wal-reader-hard-exit-20261126`.

## Scenario

The test appends one synthetic ActionAudit event, pins an independent read-only SQLite snapshot, then starts a spawned writer that appends a second event and exits immediately after native COMMIT returns, before the connection closes or the caller receives a return value.

The keeper must continue to see only the first event. TRUNCATE checkpoint remains incomplete while it is open. After last-reader close, a cold audit reader must see both committed events in order, with the second event's exact request identity, argument digest, bounded outcome and timestamp. The final checkpoint and quick_check must succeed.

## Privacy and evidence limits

The ToolCall contains a synthetic private marker; persisted SQLite files must not contain that raw argument value. ActionAudit stores a digest and bounded metadata, but this local row is not proof of an external effect, authenticated issuer, consent, permission, or a safe retry.

This is native-COMMIT process-exit plus surviving-reader/last-close regression evidence only. It is not fsync/power-loss durability, independent custody, trusted time, cross-store atomicity, or exactly-once external effects. No ActionAudit source/schema v1 DDL/public field or frozen contract changes.

No paid/external compute, credentials, hardware, Candidate, protected V2 evaluation, main write/merge, or UI/frontend work occurred. PR #8 and PR #638 remain Draft/unmerged. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no PASS is claimed.
