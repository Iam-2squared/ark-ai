# ARK Run922 — SQLite catalog UTF-8 identity admission across five disconnected core stores

**Scope:** free-only, local-first, non-UI, synthetic SQLite fixture code. No protected V2 evaluation, V3 Candidate/training, real personal-context content, permissions, action executor, or external API/GPU calls. **ARK overall NOT_PASSED.**

## Exact work basis and outcomes

Initial Draft PR #8 HEAD: `62560a377cc3dc14e1012c760a79b652dd8047c3`. Prior exact-head [CI #43905632857](https://github.com/Iam-2squared/ark-ai/actions/runs/43905632857) was checked **GREEN 6/6** (Ubuntu/Windows, Python 3.11–3.13) before changing core sources.

This invocation deliberately addressed the **same cross-store class of pre-hydration weakness**: a `sqlite_master` count and aggregate DDL SQL byte limit do not bound the separately stored `type`, `name`, and `tbl_name` catalog columns. A corrupt or adversarial local SQLite fixture could keep the DDL short while presenting a huge schema identifier to Python before the exact-schema equality check. All five stores now use a SQLite-side three-scalar aggregate in the existing transaction, with `length(CAST(value AS BLOB))` and cumulative UTF-8 byte budgets. Their exact object counts and previous DDL ceilings remain unchanged; the later frozen-schema and quick-check comparisons remain mandatory.

| Disconnected module | Source commit | Synthetic regression tests | Cases authored |
| --- | --- | --- | ---: |
| Personal Context request replay | [`fb04355b`](https://github.com/Iam-2squared/ark-ai/commit/fb04355b271bc43b6271a884be87f6a9d42fd9c5) | [`e5628603`](https://github.com/Iam-2squared/ark-ai/commit/e5628603273a52d1972e4939fe29e8f40bf8ad1f) | 6 |
| Proposal lifecycle event store | [`2a187658`](https://github.com/Iam-2squared/ark-ai/commit/2a187658bc41f206b70a68e8c40277b294ec00f0) | [`06e489dc`](https://github.com/Iam-2squared/ark-ai/commit/06e489dc94ad92d5392742f6cb0bfeea7418a2cc) | 6 |
| Detached synthetic READ journal | [`88c3f481`](https://github.com/Iam-2squared/ark-ai/commit/88c3f48139c8716762545bda89980293b3017954) | [`4e5907c5`](https://github.com/Iam-2squared/ark-ai/commit/4e5907c51f628ff1b54c92b78f4820d518815efa), corrective test commit [`22684fa1`](https://github.com/Iam-2squared/ark-ai/commit/22684fa173819f542fc2465d189377d3fc6c3b73) | 6 |
| Memory epoch witness ledger | [`aa044297`](https://github.com/Iam-2squared/ark-ai/commit/aa044297fa45cc0b8ccd0327539d90bfd0b3ddd5) | [`f88bc6b4`](https://github.com/Iam-2squared/ark-ai/commit/f88bc6b4f4baf7b353f2bb37c3987cf0a291c86e) | 6 |
| Durable synthetic WRITE slot reservation | [`f7899fbf`](https://github.com/Iam-2squared/ark-ai/commit/f7899fbf82e244a8f44ea32343216210d13a95b5) | [`d217db1a`](https://github.com/Iam-2squared/ark-ai/commit/d217db1a380ed27ee19655acfbeec40966f8aefc) | 6 |

**30 new test cases AUTHORED, not yet 30 PASS.** Every test uses only disposable or in-memory synthetic SQLite. They exercise oversized `name`, `tbl_name`, `type`, multibyte UTF-8 identities, aggregate-but-individually-moderate identity bytes, and clean read/recovery. A guard wrapper fails immediately if a malformed catalog reaches the `SELECT type,name,tbl_name,sql` Python hydration query. `PRAGMA writable_schema=ON` is used only on disposable test fixtures to simulate invalid catalog state; never on any real or existing user database.

The corrected READ journal test uses the reviewed `genesis_witness()` for an empty cold-recovery stream instead of an unavailable `witness()` instance method; no runtime source semantics or contract was altered by that correction.

## Local micro-probe, CI, and limits

A standalone Python 3.13 / SQLite 3.46.1 *SQL-only* disposable in-memory probe verified that modifying catalog `name`, `type` or `tbl_name` can yield 4,200+ UTF-8 identifier bytes while unchanged SQL DDL stays at 139 bytes, illustrating the missing boundary. This is **not** a local ARK pytest run and does not certify a commit.

At report preparation, exact source+test HEAD `d217db1a380ed27ee19655acfbeec40966f8aefc` [CI #43913161745](https://github.com/Iam-2squared/ark-ai/actions/runs/43913161745) was **QUEUED**. Earlier Run922 package CIs were IN PROGRESS or QUEUED, with no new latest-head six-matrix certification yet. The verified preceding Run921 checkpoint [CI #43905632857](https://github.com/Iam-2squared/ark-ai/actions/runs/43905632857) is **GREEN 6/6** and covers the earlier HEAD only. Regular Contents commits launched CI automatically; no manual rerun or duplicate workflow dispatch was made.

Unresolved: the intermittent cross-process WAL/SHM last-close/alias race; independent witness custody and clock trust; durable external-action exactly-once guarantees; cross-store atomicity; Planner COMMIT-UNKNOWN terminal reconciliation. Rejecting oversized catalog identifiers is only an admission control and does not establish corruption recovery, authenticated provenance, trusted time or action authorization.

## Protected boundaries and next gates

No new UI/Frontend changes. Frozen V1/V2/Local UI/Launcher evidence and contracts, V3 protected PR #5, paused UI PR #9, main, and all real-model/authorization gates remain unchanged. Draft PR #8 remains isolated and unmerged. No purchases, paid APIs/GPU, physical PC, real Candidate generation/promotion, protected evaluation, credentials, tool WRITE, automatic UNKNOWN retries, irreversible actions or data export.

**Next:** (1) inspect final exact-HEAD all-six CI and repair any failures through ordinary permitted Contents operations; (2) examine remaining SQLite catalog pre-hydration callers without repeating already-complete checks; (3) reproduce/triage the two-process ARK WAL/SHM race using disposable fixtures; (4) strengthen Memory CAS/event continuity and Planner cold COMMIT-UNKNOWN; (5) advance pinned Registry/PermissionGate/audit/mock executor integration only after lower-level exact-head GREEN.
