# Run889 — disconnected core: CI diagnostic recovery, Planner prefixes, schedule quarantine, Memory CAS/expiry

**Observed report authoring wall clock (Asia/Tokyo/JST): 2026-11-15T14:48:04.145+09:00** (derived from runtime wall clock; NOT trusted time/provenance, consent or human review). **ARK/JARVIS overall: NOT_PASSED.** No paid/external compute, new UI/frontend, real backend, credential connection, protected evaluation or Candidate training.

## Starting repo state and inherited evidence

- Initial work-basis HEAD: `89d7876b42f98d6d265a8cc4f513d36e7de53736`, branch `research/jarvis-foundations` / open Draft PR #8. Frozen V1/V2/Local UI/Launcher contracts/evidence unchanged; protected PR #5 and paused UI PR #9 both remain Draft/unmerged.
- Run888 checkpoint exact-head [CI #43678612032](https://github.com/Iam-2squared/ark-ai/actions/runs/43678612032) **FAIL 6/6**, with completed Windows/Ubuntu Python 3.11–3.13 jobs failing pytest (Ruff passed). Ubuntu 3.12 log: **2 failed, 15,929 passed, 1 skipped**. Windows 3.11 log: **2 failed, 15,831 passed, 99 skipped**. Both failures in pre-existing `tests/test_registered_disconnected_fixture_join_run519.py`, asserting `match="authority"` for a tampered denial property and a replaced negative-authority link constructor. New early guard denied safely but emitted `registered fixture link result carrier changed` instead. This is an **error-classification compatibility** regression, not evidence of backend dispatch or accepted forged authority.

## NEW, four separate free-only non-UI packages

1. **Smallest safety-preserving CI repair** — normal Contents API commit `78130d4431729dc5ed553f80e945cffa41b0d69f` changes only the early `_require_original_registered_link` diagnostic in `src/ark/agency/disconnected_registered_fixture_join.py` to `registered fixture link result carrier changed; no authority`. Both historic `authority` and new `result carrier changed` assertions now match while the same original constructor/field/getter refusal is still evaluated **before any tampered getter/constructor invocation**. No guard was removed, no real ToolBackend execute path opened.
2. **Planner journal prefix and crash-UNKNOWN** — new `tests/test_planner_prefix_divergence_restart_run889.py` committed at `811994ccda24ac86fafeb63c50f3dc8f3df092f5`: **3 authored synthetic cases** cover independently retained genesis after multiple committed events; divergence from a second SQLite journal with the same topology but different event-time hash; and a middle RUNNING step after the first dependency succeeded, remaining ambiguous after restart and not automatically retried by stale CAS. Original Planner journal source unchanged.
3. **Offline proactive scheduler triage** — new `tests/test_schedule_unknown_restart_no_authority_run889.py` committed at `5b645e9405011fe85b853fc3addf03810df94798`: **4 authored synthetic cases** distinguish `LOCALLY_QUARANTINED` / `PREEXISTING` / `UNCHANGED` / `ADVANCED_OTHER` when reconstructing an expired scheduled occurrence after restart, plus forged genesis and conflicting observed-clock denial. Every accepted result still requires manual review and denies notification, tool execution, automatic replay, trusted clock and consent. No scheduler or timer run.
4. **Memory CAS/expiry/coherent snapshot** — new `tests/test_memory_cas_expiry_snapshot_run889.py` committed at `db4f351bd343f27a7417df9856cc6d1f0abae049`: **3 authored synthetic cases** check expired memory remains revision-fenced until explicitly refreshed, an opt-in two-namespace read filters expired records using one supplied clock sample after restart, and bounded purge preserves the surviving row with terminal `expire` event. Memory v1 DDL, store source and clock trust model unchanged.

**Total: 10 newly authored cases (not ten CI-confirmed passes); one repaired implementation error text, three new synthetic test files.** No local full-repo tests were executed in this run; GitHub Actions exact-head matrix is the verification authority. This report does not upgrade any PASS label.

## CI overlap/evidence as actually observed

- [CI #43682284234](https://github.com/Iam-2squared/ark-ai/actions/runs/43682284234) on `78130d443...`: **IN PROGRESS** at report observation.
- [CI #43682403232](https://github.com/Iam-2squared/ark-ai/actions/runs/43682403232) on `811994cc...`: **IN PROGRESS**.
- [CI #43682474205](https://github.com/Iam-2squared/ark-ai/actions/runs/43682474205) on `5b645e94...`: **IN PROGRESS**.
- [CI #43682543816](https://github.com/Iam-2squared/ark-ai/actions/runs/43682543816) on `db4f351b...`: **QUEUED**.
- Report/checkpoint commits trigger automatic CI as well. **All six jobs GREEN on the last exact HEAD is NOT YET CONFIRMED**. No duplicate manual run was started. Different-head partial results must not be spliced together.

## Frozen boundaries, unsolved blockers, next plan

All UI/frontend development remains paused; Draft #9 untouched. Draft #5 training gate untouched and unmerged. No real external or paid GPU/API/service, subscriptions, Candidate adapters/weights, protected V2 evaluation, promotion, secrets, physical PC tests, real READ/WRITE effects, automatic ambiguous-action replay, destructive mutation, frozen-contract change, or main merge. Inert hashes are not independent provenance or trusted clock.

**Open blockers:** Windows SQLite WAL/SHM last-close transient inode race, cross-process Privacy Revocation losing-process rejection, unknown COMMIT outcomes/cross-store atomic exactly-once, independent custody and authentic consent, target-PC GGUF gate. Do not retry ambiguous WRITE or relax symlink/hardlink/orphan veto.

**Next plan / 今後の方針:** (1) verify newest exact-head six-job GREEN or investigate actual FAIL, repairing only via normal allowed path; (2) isolate Privacy Revocation SQLite race with privacy-safe postfailure observations; (3) extend Memory generation/CAS/expiry and Planner terminal/UNKNOWN recovery; (4) connect Registry/PermissionGate/durable occurrence/audit-before-action/Mock only after lower-level exact-head GREEN; (5) continue observation/proactive/Context fixtures and detached free-only V3 guards without UI work.
