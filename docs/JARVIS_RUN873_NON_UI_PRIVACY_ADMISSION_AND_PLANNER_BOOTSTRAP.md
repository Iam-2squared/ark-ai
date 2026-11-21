# Run873 — Non-UI privacy admission and Planner bootstrap boundaries

## Scope and preserved authority

This invocation began from 3471323ae16ce465f18faa721fdda28f45ae9ff1, the Run872 checkpoint, whose [CI #43597453225](https://github.com/Iam-2squared/ark-ai/actions/runs/43597453225) is **GREEN 6/6** (Ubuntu/Windows, Python 3.11/3.12/3.13). That CI covers only the prior HEAD. Work remains on [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8); frozen V1/V2/Local UI/Launcher, Draft PR #5 (protected V3) and paused Draft PR #9 (UI) are untouched. ARK/JARVIS is **NOT_PASSED**. All work is synthetic, local-first, denial-only and free-only. It proves neither trusted consent nor future OS/file custody, tool authorization, trained weights, a trusted clock, real effects, or external exactly-once.

## Implemented — three source changes, three regression modules

1. **Personal Context revocation veto**, source c739ac6d89b82ce04e7ebac237bf22108bfd325f, tests 0cc51440f03e733d162e78d6d4f61dd89db1cd61: unversioned schema existence uses SQLite SELECT 1 FROM sqlite_master LIMIT 1; PRAGMA quick_check reads at most two diagnostics. Five authored synthetic cases cover valid bounded diagnosis, extra bad diagnostics, guarded bootstrap, planted TABLE/VIEW refusal without repair. Append-only veto, digest, ordering, row preflight and no-regrant unchanged.
2. **Disconnected privacy veto**, source 13374a29506cded86d0d45373a4558678515a4c1, tests b513b34e48657f6436941b0a8d5dea91feb135f7: before DDL hydration cap SQLite catalog at 8 objects / 8192 bytes, quick_check at two rows; before owner/scope history hydration, SQL-admit at most 512 rows, exact storage classes and fixed 64 UTF-8-byte digest widths, with timestamp range. Unversioned bootstrap uses one-row SQLite catalog existence. Ten authored cases cover clean/rejected diagnostics, foreign objects, bootstrap, 9 KB DDL, malformed digest/clock, and 513 rows. Existing sequence, order, duplicate checks and deny-only properties remain active. Standalone SQLite syntax smoke confirmed catalog count 2, valid row admission (1,0), malformed row admission (1,1). This is not full pytest.
3. **Planner crash journal bootstrap**, source 124e5d4e26b0ca71c3fffc48df120ead5370ba93, tests ad35c8cd6f46420c8891d5c6e48546e7d06770c1: replace unversioned full object iteration with SQLite SELECT 1 FROM sqlite_master LIMIT 1 in existing BEGIN IMMEDIATE. Five authored cases cover clean inert recovery, planted TABLE and VIEW refusal without repair, no pre-bootstrap DDL hydration, and post-bootstrap schema validation. Terminal propagation, UNKNOWN quarantine, transition chain and no executor unchanged.

Six modified/new paths independently reread at source/test HEAD ad35c8cd6f46420c8891d5c6e48546e7d06770c1. Comparison with initial basis returned **exactly** three non-UI Python files and three new non-UI test files; no lines over 100 chars. **20 tests authored, NOT 20 proven passed.** No complete local pytest/Ruff or physical-PC evidence. GitHub CI is cross-platform test gate.

## Independent read-only review of prior privacy concurrency failure

Older [CI #43596487033](https://github.com/Iam-2squared/ark-ai/actions/runs/43596487033) had Ubuntu 3.13 and Windows 3.11 failures; Ubuntu 3.13 reported **15,516 passed, one failed, one skipped**. The lone failed prior test was test_privacy_revocation_cross_process_run425.py, where the losing subprocess rejection did not match its expected already-revoked string. The captured stderr was truncated as LOSER_REJECTION_DETAIL:'un...' — **the exact rejection cause was not recovered**. One durable REVOKED row appeared, but a failure or committed-row observation is neither consent nor authorization to retry. Do not call this proven WAL/SHM last-close, and do not weaken durable revocation, UNKNOWN or no-retry gates. The later exact Run872 checkpoint CI succeeded.

## CI observations and next plan

Automatic CI is triggered by normal Contents writes only, with no manual equivalent rerun. Source/test HEAD ad35c8cd6f46420c8891d5c6e48546e7d06770c1, [CI #43602194626](https://github.com/Iam-2squared/ark-ai/actions/runs/43602194626), was **QUEUED** at last exact observation. Intermediate privacy-veto test HEAD b513b34e48657f6436941b0a8d5dea91feb135f7, [CI #43601986135](https://github.com/Iam-2squared/ark-ai/actions/runs/43601986135), had Ubuntu Python 3.11 and 3.13 GREEN; others in progress then. No intermediate GREEN applies to latest HEAD.

1. Verify the newest exact-HEAD six-job Ubuntu/Windows CI. Repair genuine failure only through normal GitHub Contents writes.
2. Deterministically isolate the previously observed revocation loser result and its durable row outcome; do not relax fail-closed denial.
3. Investigate Memory/ActionAudit independent WAL/SHM final-close and COMMIT-UNKNOWN, Planner manual-only UNKNOWN, Memory coherent CAS/expiry.
4. Integrate immutable ToolRegistry, exact-type PermissionGate, durable occurrence/audit-before-action and disconnected/mock executor after prerequisite GREEN.

## Blockers

Full latest six-environment CI pending; SQLite pathname races, independent witness custody, trusted clock/permission, cross-store atomicity and external effect exactly-once remain unresolved. No paid service, external GPU/compute, protected evaluation, Candidate generation/promotion, new secrets, UI, destructive operation or main merge.
