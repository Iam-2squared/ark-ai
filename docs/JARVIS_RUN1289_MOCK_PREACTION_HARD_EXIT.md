# JARVIS Run1289 — Mock executor pre-action-audit COMMIT hard-exit regression

## Exact basis

- Repository: `Iam-2squared/ark-ai`.
- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `08d7bd7a89da786e0773dabead86d3adad40e98e`.
- Rebased test-only package from Draft PR #455, whose prior child head was `b726242f5015210879affdc2a382917aba4f49fe` on older parent `126f7df3ab83013aa2f456b305d364013f7bfd19`.
- No executor, ActionAudit, occurrence, registry, permission, schema, DDL, API, or frozen-contract change.

## Regression coverage

A spawned interpreter exits immediately after the native ActionAudit transaction COMMIT returns, before `append()` returns to the executor. Profile sentinels verify the real process-local PermissionGate and ActionAudit append were reached while the disconnected mock backend was not called. Cold recovery must retain exactly one durable occurrence reservation and one `mock_pre_action` event, with no completion event. A fresh executor retry using the same one-shot token and a different occurrence ID must be denied before consuming the new process-local gate or calling the mock backend.

## Evidence boundary

Synthetic local SQLite and the disconnected mock backend only. This covers process exit after successful native COMMIT; it does not establish fsync/power-loss durability, trusted time, authenticated consent, cross-store atomicity, real dispatch, or exactly-once external effects.

The prior PR #455 exact-head CI was GREEN on its older parent only and does not transfer. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no local pytest/Ruff PASS is claimed.

No paid/external compute, Candidate generation/promotion, protected V2 evaluation, credentials, hardware, destructive action, frozen-contract change, UI/frontend work, or main merge. PR #5/#8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
