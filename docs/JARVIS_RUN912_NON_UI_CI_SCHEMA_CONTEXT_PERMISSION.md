# ARK AI Run912 — non-UI schema CI repair, retained-context privacy, registered clock preaccess

**Date:** 2026-11-16 JST. **Branch:** `research/jarvis-foundations`, Draft PR #8; **starting exact basis:** `4afb0bce595b61769e70053e6ff624d5f9d2cbac`. **Scope:** synthetic/local, free-only backend development. No UI, paid compute, credentials, external ToolBackend, private user data, protected evaluation, model Candidate, or main merge.

## 1. Exact Run911 CI failure and semantics-preserving repair

Run911 final checkpoint [Actions #43801587220](https://github.com/Iam-2squared/ark-ai/actions/runs/43801587220) **FAIL all six** Windows/Ubuntu × Python 3.11–3.13 jobs, caused by the **same two** parametrized tests in `tests/test_disconnected_schema_catalog_name_budget_run911.py`. The isolated `PRAGMA writable_schema=ON` + `UPDATE sqlite_master` test fixture left a Python SQLite implicit write transaction open. The **production** `capture_disconnected_sqlite_schema()` correctly rejects non-idle connections with `exact idle SQLite connection required` **before** preflight; tests incorrectly expected `preflight exceeds byte budget`. Not a demonstrated production fail-open.

[Ordinary Contents API fix `34d13703`](https://github.com/Iam-2squared/ark-ai/commit/34d13703e500613a78846503f0fe679fbe1e37ee) explicitly commits the disposable synthetic catalog update before entering query-only mode, with assertions that the setup had a transaction and is now idle. The preflight remains tested under the intended idle-connection contract, without relaxing production SQL budgets, alias handling, existing schema, authorization or denial. Independent local CPython SQLite exercise observed that both corrupt `name` and `tbl_name` fixtures start in a transaction and their metadata bytes total 66,044, over the 65,536-byte cap, after the explicit COMMIT. **Full pytest CI is still necessary.**

## 2. Personal Context retained receipt cannot restore revoked scope or expired content

[Seven-case new regression `278ee0e5`](https://github.com/Iam-2squared/ark-ai/commit/278ee0e5500ad5bccf60aeb71b5c8ac2ecd56e9c) covers synthetic retained preview verification after six changes: scope removed, owner changed, observation clock reaches expiry, local content changed, local content hash changed, or receipt digest replayed. A seventh unchanged source verifies locally. Every preview retains explicit `consent_verified=False`, `external_export_authorized=False`, `tool_dispatch_authorized=False`, `retention_authorized=False`. Only existing detached public helpers and synthetic records are used; no actual user context is read or written. These tests do not imply a trusted clock, revocation certificate, or consent.

## 3. Registry-bound PermissionGate exact clock admission before callbacks

[Thirteen-case new regression `a8a0b32e`](https://github.com/Iam-2squared/ark-ai/commit/a8a0b32e2fae1684fff548044b81a0188ab72bca) covers six invalid `now_ms` values for both READ and WRITE registrations: bool true/false, negative, over SQLite signed range, string and float. A deliberately poisoned registry.bind and grant generator must never execute before rejection. Valid local READ remains registry-bound, exact-scope and disconnected. No persisted token, signed authorization, real backend dispatch or durable exactly-once proof is inferred.

**Total:** 20 newly authored parameterized regression cases (7 Personal Context + 13 gate) and two existing failed schema cases repaired; **do not count tests authored as CI PASS.** Normal GitHub Contents API was used after fresh Draft PR #8 HEAD rereads. No force push, raw Git-object bypass, manual duplicate CI or frozen changes.

## 4. Free-only, immutable boundaries and open work

V1/V2/Local UI/Launcher evidence frozen. Protected V2 final evaluation and Draft V3 PR #5 gates closed. Draft UI PR #9 untouched; UI development paused. Main unchanged; Draft PR #8 unmerged. No paid services/GPU/API, new accounts/secrets, real Candidate adapters/weights, Candidate promotion, physical machine actions, real WRITE, private data capture or protected evaluation.

Unresolved: intermittent Windows/Ubuntu SQLite WAL/SHM last-close revocation/alias race (durable REVOKED with another SIDECAR_REFUSED remains **ambiguous/fail**, never success/replay), independent file/provenance custody, Planner cross-store COMMIT-UNKNOWN, Memory CAS/expiry/event integrity, trusted-clock audit-before-action and exactly-once external effects. In-process hashes and synthetic test witnesses cannot establish independent identity or consent. Overall ARK/JARVIS: **NOT_PASSED**.

## 5. CI and next work

At this report's composition, automatically triggered PR runs for schema-fix [#43806245768](https://github.com/Iam-2squared/ark-ai/actions/runs/43806245768), Personal Context [#43806501547](https://github.com/Iam-2squared/ark-ai/actions/runs/43806501547), and Gate [#43806660513](https://github.com/Iam-2squared/ark-ai/actions/runs/43806660513) were **IN PROGRESS**; no latest-head six-job GREEN is claimed. The report and later canonical checkpoint commits will each get distinct HEADs/runs, which must be checked separately.

**Next plan / 今後の方針:** (1) validate exact repaired/latest HEAD six-job CI, narrowly repair any confirmed failures while continuing independent backend work; (2) use disposable WAL failure-phase evidence to isolate cross-process last-close race with strict sidecar rejection unchanged; (3) strengthen Memory atomic CAS/expiry/events and Planner terminal/restart UNKNOWN propagation; (4) after the lower-layer exact-head GREEN integrate ToolRegistry, PermissionGate, restart-safe audit-before-action and disconnected mock executor, never live WRITE; (5) continue privacy-safe Context and proactive/observation contract fixtures, V3 free-only identity/approval guards, keeping PR #5/#8/#9 Draft/unmerged and UI paused.
