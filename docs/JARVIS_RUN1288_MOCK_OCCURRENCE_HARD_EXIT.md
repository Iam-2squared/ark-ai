# JARVIS Run1288 — Mock executor occurrence-COMMIT hard-exit regression

## Exact basis

- Repository: `Iam-2squared/ark-ai`.
- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `08d7bd7a89da786e0773dabead86d3adad40e98e`.
- Rebased test-only package from Draft PR #454, whose prior child head was `c13240edb20abca99b287ccc94074583da8e75f6` on older parent `126f7df3ab83013aa2f456b305d364013f7bfd19`.
- No executor, occurrence ledger, ActionAudit, PermissionGate, ToolRegistry source, schema, DDL, API, or frozen-contract change.

## Regression coverage

A spawned interpreter exits immediately after the synthetic durable occurrence reservation's native SQLite COMMIT returns, before the reservation receipt reaches the executor. Process-local sentinels verify that PermissionGate consumption, ActionAudit append, and the disconnected mock backend have not run. Cold recovery must retain exactly one occurrence reservation, show no audit event, and reject the same one-shot token with a different occurrence ID before a fresh gate, audit, or backend call.

## Evidence boundary

Synthetic local SQLite and the disconnected mock backend only. This covers process exit after a successful native COMMIT; it does not establish fsync/power-loss durability, trusted time, authenticated consent, cross-store atomicity, real dispatch, or exactly-once external effects.

The prior PR #454 exact-head CI was GREEN on its older parent only and does not transfer. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no local pytest/Ruff PASS is claimed.

No paid/external compute, Candidate generation/promotion, protected V2 evaluation, credentials, hardware, destructive action, frozen-contract change, UI/frontend work, or main merge. PR #5/#8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
