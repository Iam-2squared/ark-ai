# ARK AI Run894 — retained Planner JSON, Memory expiry CAS and privacy-bounded readback

**Observed at (Asia/Tokyo/JST): 2026-11-15T19:50:43.046+09:00.** Ordinary wall clock, not trusted action/consent time. **ARK/JARVIS NOT_PASSED.** No UI/frontend work, paid/external GPU, provider calls, real ToolBackend, Candidate generation, human approvals or main merge.

## Exact repository and established CI basis

Starting branch / Draft PR #8: `research/jarvis-foundations` at `ba1700618096061d70da08acf1751f8b8cf2eb64`, prior Run893 checkpoint; Draft PR #5 and paused UI Draft PR #9 were untouched. GitHub CI [#43702380216](https://github.com/Iam-2squared/ark-ai/actions/runs/43702380216) is **GREEN 6/6** at that exact starting HEAD: Ubuntu/Windows and Python 3.11/3.12/3.13. This does not certify subsequent commits.

## NEW — three independent non-UI coherent work packages, 14 authored tests

1. **Planner: re-admit original nested JSON proxy backing before digest.** Source `src/ark/agency/planner.py` commit `df54f2d65d57c891929d742fd7b1a4beabf1be25`, tests `tests/test_planner_mutable_proxy_backing_run894.py` at `af2a13f9b285e48d0dcb002c72a386c86b1dc43e` (9 cases). A reflectively installed MappingProxyType can retain a separately mutable backing dictionary; mere `call.arguments is original` does not prove its nested values remain safe. Before every later `ToolCall.request_id` traversal in `PlanGraph._assert_plan_epoch`, re-run the existing exact-type, finite-numeric, nesting, byte and node admission. Tests fault-inject callback-bearing values, NaN, huge integers, foreign mappings and unpaired Unicode, then confirm no hash callback or state transition. Bounded but different exact values still fail request identity. Normal canonical request hashes, frozen ToolCall/PlanStep contracts and external execution authority are unchanged. No cross-interpreter identity attestation is claimed.

2. **Memory: independent-process expiry refresh / stale CAS.** `tests/test_memory_cross_process_cas_restart_run893.py` extended at `b5b1b04975995e8b8e61aaf919277afe26b16546` (2 cases). A separate interpreter refreshes an expiring row; a later parent purge must not delete the nonexpiring successor or append a false expiration event. Conversely, after committed expiration, stale child CAS at the old revision must not resurrect the row or consume an event sequence. Disposable SQLite/fake owner/clock only. No Memory schema/source modifications, trusted-clock claim or cross-store exactly-once claim.

3. **Privacy: bound disposable WAL verifier's SQLite hydration.** `scripts/diagnose_revocation_wal_processes.py` source commit `0cf3f07fc6a81106ac0922091ba7c2c265efc242`; `tests/test_revocation_wal_bounded_readback_run894.py` added at `dceb4c9d1f90f852c029d9ff60c91e7579ad4007` (3 cases). A one-row/two-schema-object/one-quick-check proof only needs bounded readback: `fetchmany(2)` veto rows, `fetchmany(3)` catalog objects and `fetchmany(2)` quick-check messages. Tests cover exact synthetic one-row veto, extra veto and unexpected schema object. Existing verify-false-on-ambiguity, sidecar refusal, read-only opening, no private path export, no retry and exit-code behavior preserved. This is a *diagnostic*, not a fix for the Windows WAL/SHM disappearing-inode last-close race or externally authenticated veto.

**14 authored regression cases are not automatically 14 passing cases.** The last complete new source/test HEAD is `dceb4c9d1f90f852c029d9ff60c91e7579ad4007`. Automatic GitHub CI runs:
- Planner source [#43705481082](https://github.com/Iam-2squared/ark-ai/actions/runs/43705481082) — IN PROGRESS when sampled, Ubuntu 3.11/3.13 GREEN, remaining four not certified.
- Memory tests [#43705564682](https://github.com/Iam-2squared/ark-ai/actions/runs/43705564682) — IN PROGRESS when sampled, Ubuntu 3.12/3.13 GREEN.
- Planner tests [#43705636027](https://github.com/Iam-2squared/ark-ai/actions/runs/43705636027) — IN PROGRESS when sampled, Ubuntu 3.11 GREEN.
- Privacy source [#43705788638](https://github.com/Iam-2squared/ark-ai/actions/runs/43705788638) — IN PROGRESS when sampled.
- Privacy tests [#43705837371](https://github.com/Iam-2squared/ark-ai/actions/runs/43705837371) — QUEUED when sampled.

No duplicate manual workflow run. These snapshot statuses may be superseded by later CI; follow the exact-head checks rather than transfer earlier GREEN. The technical report and final checkpoint will themselves trigger automatic CI.

## Immutable boundaries, unresolved blockers, next plan

Frozen V1/V2/Local UI/Launcher evidence and evaluations, direct Observation v1 and Memory v1 DDL are unchanged. Draft PR #5 remains protected and unmerged; Draft PR #9 is paused/unmodified/unmerged; Draft PR #8 remains isolated/unmerged. No new paid service, real Candidate/weights, protected V2 final evaluation, promotion, physical-PC test, credentials or secrets, real write/dispatch, automatic retries of ambiguous commits or irreversible operation.

**Blockers:** trusted clock/consent and independently held privacy evidence; cross-store COMMIT-UNKNOWN; Windows SQLite WAL/SHM last-close/refusal despite durable winning row; real hardware offline GGUF gate. Hash/readback of synthetic local fixtures does not independently authenticate a person, authorize an action, or establish externally verified outcomes.

**Next plan / 今後の方針:** (1) verify latest exact-head six CI jobs and minimally repair any failures via the normal Contents API; (2) investigate bounded WAL last-close/loser-versus-durable-veto behavior without permissive retries; (3) add retained nested Planner argument/witness integrity and crash UNKNOWN recovery; (4) advance Memory coherent snapshot/expiry and Registry/PermissionGate durable audit-before-action disconnected bridge only after exact-head evidence; (5) pursue independent privacy-safe Personal Context, proactive scheduling and Observation backend contracts, and free V3 guard work without changing frozen contracts or UI.
