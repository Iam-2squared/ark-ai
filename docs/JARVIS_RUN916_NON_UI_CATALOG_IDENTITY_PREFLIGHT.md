# ARK AI Run916 — disconnected SQLite catalog identity prehydration

Prepared 2026-11-16 JST. Four **independent, reversible, non-UI** foundation packages use only original GitHub Contents writes and synthetic SQLite fixtures. No paid/external GPU, account connection, real user data, operational tool, protected evaluation, Candidate, or material migration.

## Basis and bounded risk

- Initial branch and Draft PR #8 HEAD: `7414ef798addfc86852677e2680787a6430b0259`. Previous exact Run915 checkpoint CI [#43828669061](https://github.com/Iam-2squared/ark-ai/actions/runs/43828669061) **GREEN 6/6**, Windows/Ubuntu × Python 3.11–3.13, **only for that old head**.
- The existing SQLite catalog preflights capped object count and total DDL SQL bytes, but did **not** constrain `sqlite_master.type`, `name`, or `tbl_name` when malformed stored identities are large while DDL remains short. That allowed unnecessarily large Python hydration before exact frozen-DDL comparison. New checks bound aggregate UTF-8 **BLOB** bytes in SQLite, before the comparison, in the same transaction/snapshot. Small hostile fields with a large **combined** size are rejected; Unicode is measured in bytes rather than characters.
- All four source changes preserve the original persisted DDL/schema versions, object counts, DDL byte maxima, read-only/denial semantics, and automatic UNKNOWN no-replay. This is **prehydration memory safety**, not independent provenance, a storage anti-rollback proof or execution authority.

## Packages — 24 authored regression cases

1. **Disconnected due-slot reservation**: [source `efbffc1d`](https://github.com/Iam-2squared/ark-ai/commit/efbffc1d12814203a7905ace2d4e45e510758e48), [6-test `8a76b6f1`](https://github.com/Iam-2squared/ark-ai/commit/8a76b6f11b7e66deae7d888e9852354dd8521122). Adds aggregate 4,096-byte `type/name/tbl_name` preflight while keeping two-object and 4,096-byte DDL limits. Tests all three malformed fields, UTF-8 multibyte overflow, split-field aggregate overflow, and intact frozen DDL. The test connection refuses catalog hydration on the unsafe paths.
2. **ActionAudit v1**: [source `8eaa919a`](https://github.com/Iam-2squared/ark-ai/commit/8eaa919a4d0054ad1b95e8806bbb9de3444b1425), [6-test `d1a9609a`](https://github.com/Iam-2squared/ark-ai/commit/d1a9609af585519f0770608e77f887c9eb44c76f). Adds aggregate 16,384-byte stored identity cap with existing 16-object / 16,384-byte DDL caps unchanged. Rejects malformed stored identifier data before `fetchall`, while a normal small SQLite catalog still returns normalized rows.
3. **Proactive quarantine ledger**: [source `9e5e7550`](https://github.com/Iam-2squared/ark-ai/commit/9e5e75503e94bb88b64fa0f838a90cf75593ad5a), [6-test `34df3f9d`](https://github.com/Iam-2squared/ark-ai/commit/34df3f9da8426ea0735c587952e4922ba65c671b). Adds 8,192-byte stored catalog identity preflight in the same SQLite transaction; retains 8-object / 8,192-byte DDL limits and inert quarantine receipts. Normal create+restart remains a positive control.
4. **Occurrence reservation anti-replay ledger**: [source `901b38a0`](https://github.com/Iam-2squared/ark-ai/commit/901b38a019c0842649c850474e4f0fc08edbcbf3), [6-test `28816537`](https://github.com/Iam-2squared/ark-ai/commit/288165375c0da458bf4050b8dae04ba0f0c1844a). Adds 8,192-byte aggregate stored metadata bound to `_objects`, retaining exactly three catalog objects and 8,192-byte DDL limit. Normal frozen schema and inert no-dispatch replay review remain unchanged.

Each test file contains five negative synthetic corruption cases (three single-field, one multibyte, one split cumulative) and one positive control. Tests are **authored**, not claimed all-platform passed. No real database corruption, migration or tool effect; `PRAGMA writable_schema` is used only for disposable `:memory:` fault injection.

## CI evidence (observed 2026-11-16 18:02 JST)

- Baseline [Run915 CI #43828669061](https://github.com/Iam-2squared/ark-ai/actions/runs/43828669061) **GREEN 6/6** for `7414ef79...`, not Run916.
- Due source [#43834963143](https://github.com/Iam-2squared/ark-ai/actions/runs/43834963143): **IN PROGRESS**, 3/6 jobs GREEN, zero observed failures.
- Due test [#43835098062](https://github.com/Iam-2squared/ark-ai/actions/runs/43835098062): **IN PROGRESS**, 2/6 jobs GREEN, zero observed failures.
- Audit test [#43835346676](https://github.com/Iam-2squared/ark-ai/actions/runs/43835346676): **IN PROGRESS**, 1/6 GREEN, zero observed failures.
- Quarantine test [#43835631097](https://github.com/Iam-2squared/ark-ai/actions/runs/43835631097): **IN PROGRESS/QUEUED**, no completed job observed.
- Occurrence test [#43836138540](https://github.com/Iam-2squared/ark-ai/actions/runs/43836138540): **QUEUED**, no completed job observed.
- Technical report and canonical checkpoint will trigger separate CI heads. **Full Run916 all-six GREEN unverified.** No duplicate workflow run was manually started.

## Frozen boundaries / next work

V1/V2/Local UI/Launcher evidence, protected V2 final evaluation, V3 Candidate/path/provenance/approval/reproducibility contracts, protected Draft PR #5, paused UI Draft PR #9 and main remain untouched. PR #8 stays Draft/unmerged. No external effect, trusted audit-clock claim, independent custody proof, automatic UNKNOWN replay, Candidate promotion, main merge or billed action. Known WAL/SHM last-close process/sidecar race remains **UNKNOWN/FAIL**, not fixed by a catalog memory budget.

Priorities: certify exact latest-head CI; investigate failures without relaxing rejection; isolate WAL/SHM last-close constructor/read/alias phases in disposable two-process fixtures; continue Memory CAS+expiry+event and Planner COMMIT-UNKNOWN recovery; only after lower-level exact-head GREEN consider registry-bound permission, audit-before-action, disconnected mock integration. Preserve UI pause and free-only boundaries. Overall ARK/JARVIS **NOT_PASSED**.
