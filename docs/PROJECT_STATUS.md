# ARK AI — Canonical Project Status

**LATEST — Run644 / 2026-11-06 JST: non-UI mock crash-regression fix, Memory event-prefix carrier hardening, cross-handle integrity tests, and Planner competing-terminal recovery tests saved.** **15 newly authored tests** plus three targeted corrections (one old mock-link test expectation and two old Memory getter-callback assertions). This is a count of test cases/repairs, **NOT a pytest PASS claim**. PR #8 remains Draft/unmerged and the latest exact-head six-job CI is **NOT GREEN yet / IN PROGRESS**. UI remains PAUSED. ARK/JARVIS/V3 **NOT_PASSED**.

**Saved at:** **2026-11-06T07:51:35.777+09:00 Asia/Tokyo/JST** (runtime UTC clock sampled immediately before this ordinary GitHub Contents update; not an action-authority/trusted clock or human approval).

## LATEST — branch, exact basis and checkpoint authority

- **Branch / PR:** `research/jarvis-foundations` / [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8), OPEN, unmerged.
- **Invocation work-basis HEAD:** `7e05e35a353f960beea334b688278d0b949220cf` (Run643 checkpoint).
- **Checkpoint write-basis HEAD:** `90694a70e84b991edf261f24766b5feda4d9eaf4` — freshly re-read before this write; all new source, tests and the technical report already saved on this head.
- **Checkpoint-result HEAD:** GitHub allocates the final commit SHA **after** the Contents API update; it is *not* prematurely embedded in this document. Use the write response and re-read live PR head to identify it. The checkpoint blob SHA at read was `3136b2532afc98fcb34d2d493695b2a04139f7d0`.
- **Previous checkpoint with full Run643 context:** [Run643 PROJECT_STATUS](https://github.com/Iam-2squared/ark-ai/blob/7e05e35a353f960beea334b688278d0b949220cf/docs/PROJECT_STATUS.md). Historical Run639 archive [part 1](status_archive/PROJECT_STATUS_THROUGH_RUN639_PART1.md) and [part 2](status_archive/PROJECT_STATUS_THROUGH_RUN639_PART2.md) are preserved and untouched.
- **Detailed Run644 report:** [JARVIS_RUN644_NON_UI_MOCK_LINK_PREFIX_CUSTODY_PLANNER_TERMINAL.md](JARVIS_RUN644_NON_UI_MOCK_LINK_PREFIX_CUSTODY_PLANNER_TERMINAL.md).

## NEW work this invocation — saved, not automatically approved

1. **Crash boundary test for synthetic WRITE audit-link sequence, test-only fix** `3cf06f2e5f068e17fc6dfb4c0b0030b3dbc1e1c2`. Inherited [Run643 CI #42117507469](https://github.com/Iam-2squared/ark-ai/actions/runs/42117507469) was **6/6 FAIL**; Ubuntu 3.11 **9,191 PASS / 1 FAIL / 1 SKIP**. `after_mock_marker` happens after a durable audit-link record is committed. Therefore the cold-restart expectation for that fault must be **1**, not 0. Only the erroneous parameterized test assertion changed; neither production ordering nor safety was weakened.
2. **Memory event-prefix witness/return carrier custody, source** `04e396bf9139f88a90f9be9c0e50e7a05337d2f8` in `src/ark/memory/sqlite_event_prefix_review.py`. Pins original field descriptors and class-local interception hooks for witness and comparison objects, rejects forged retained fields *before reading them*, and revalidates comparison carrier after its constructor callback. No Memory schema/DDL or frozen contract changes.
3. **Memory carrier regression suite**, commit `f1d78fd36dbc07077a97da49020b165a5d296882`, `tests/test_memory_event_prefix_carrier_preaccess_run644.py`. **9 authored cases** cover three witness fields, four result fields, a reentrant comparison digest mutation and unmodified read-only behavior. No inherited `__new__` mutation introduced.
4. **Memory cross-handle event-prefix continuity suite**, commit `7abee38cbffce2795b4c2cbb3e72bc5b03d5b8d8`, `tests/test_memory_event_prefix_two_handle_integrity_run644.py`. **4 authored cases** cover two owners and independently opened SQLite handles, an earlier event timestamp rewrite after a later append, and an unrelated database with the same event count. A locally valid append is never authenticated historical authorship or disclosure permission.
5. **Planner simultaneous terminal outcome race suite**, commit `206094e8ecea26d267d8a87f80a6dea47e306de3`, `tests/test_planner_competing_terminal_restart_run644.py`. **2 authored cases** require that competing FAILED/CANCELLED vs SUCCEEDED writes to one RUNNING step create exactly one durable terminal event and coherent descendant cascade across restart; stale loser cannot append. No ToolBackend or real action.
6. **Existing Memory callback tests realigned to safe earlier denial**, test-only fix `bcf4da3f3920881b440e3499403cb1a919b8dd8f`. CI exposed two Run611 expectations requiring a malicious `__getattribute__` callback to execute before rejection. The new pre-access guard prevents both executions; only the expected injection counts were updated from one to zero. Source policy unchanged.
7. **Technical report corrections** `e9fc9c7cad98afbe21da7f109795f05f649db862` and `90694a70e84b991edf261f24766b5feda4d9eaf4`; detailed evidence and exact limitations kept separate from the single canonical latest status.

## CI / evidence — accurate observed state, no false PASS

- [Inherited Run643 CI #42117507469](https://github.com/Iam-2squared/ark-ai/actions/runs/42117507469): **6/6 FAIL** from the old mock-link count assertion.
- [Mock-link-only repair CI #42123621367](https://github.com/Iam-2squared/ark-ai/actions/runs/42123621367): **Ubuntu 3/3 GREEN, Windows 3 IN PROGRESS** at observed job read.
- [Memory source #42123821795](https://github.com/Iam-2squared/ark-ai/actions/runs/42123821795): **Ubuntu 3/3 FAIL**, 2 old getter-order assertions per Python 3.11; the source hardening remains fail-closed.
- [Memory carrier test #42123928161](https://github.com/Iam-2squared/ark-ai/actions/runs/42123928161): **Ubuntu 3/3 FAIL**, same 2 assertions; Ubuntu 3.11 **9,199 PASS / 2 FAIL / 1 SKIP**. All 9 new cases were present, but not claimed universally PASS.
- [Combined source/test CI #42124289369](https://github.com/Iam-2squared/ark-ai/actions/runs/42124289369): Ubuntu 3.11 **9,205 PASS / 2 FAIL / 1 SKIP**, same earlier assertions; **test-only correction saved after this run started**.
- [Corrected test source HEAD CI #42124582916](https://github.com/Iam-2squared/ark-ai/actions/runs/42124582916): **all 6 jobs QUEUED** at latest verified read. The technical-report commit and this checkpoint may trigger later workflows; never duplicate-dispatch an equivalent workflow.
- **Exact newest checkpoint HEAD 6/6 GREEN not verified**. Remote GitHub Actions is the only executed pytest/Ruff path: local `git` cannot resolve github.com and no local test execution is claimed.
- Local-only mock, event witness, hash, clock and journal receipts cannot establish cross-database atomicity, physical user identity/consent, external exactly-once effects or action permission. No automatic retry of UNKNOWN effects.

## Frozen controls, cost and authorization boundaries

- `main` `7a843f17eb96ed13d66f23b58b06406b3002e405` unchanged. [Draft PR #5](https://github.com/Iam-2squared/ark-ai/pull/5) at `805b377697472268db02650a89c7a94b1c5337c8`, [Draft PR #9](https://github.com/Iam-2squared/ark-ai/pull/9) at `3b49048dd70eebcb6268299b9ecef4e301bbc0fd`; both untouched, Draft/unmerged. PR #8 is also Draft/unmerged.
- Frozen V1/V2/Local UI/Launcher contracts, evidence and protected V2 final evaluation untouched. **ALL new UI/frontend work paused**; PR #9 never modified.
- No paid API/service, external GPU, real Candidate training/adapter/weight generation, model promotion, credential or account connection, human-review fabrication, new irreversible architecture, live backend dispatch, physical-PC actuation or main merge.
- PR #5 pre-paid gate still lacks approved immutable runtime/model bytes and human dataset decisions, exact environment identities and spend/billing authorization. Do not open it or guess any identity.

## Next plan / 今後の方針

1. Check exact-source/test correction CI `bcf4da3f...` and checkpoint workflows when finished; inspect actual Linux/Windows job logs on any FAIL and make minimal behavior-preserving repairs via normal safeguarded Contents writes. Keep no latest PASS claim until all six jobs GREEN at a known exact HEAD.
2. Continue Memory CAS/COMMIT-UNKNOWN manual triage, local event/row snapshot integrity and retained prefix proof with competing SQLite writers. Never infer writer attribution or permission from hashes alone.
3. Continue Planner UNKNOWN/terminal persisted recovery, independent dependency cascade and corrupted retained-tip rejection, without automatic replay.
4. After relevant exact-head GREEN evidence, extend disconnected immutable ToolRegistry / exact-type PermissionGate / restart-safe occurrence reservation / persisted audit-before-mock-action. Separate databases do not confer real exactly-once.
5. Advance privacy-safe Personal Context, proactive/readiness and observation back-end fixtures, and read-only V3 free-only guards while preserving all frozen contracts and avoiding UI work.
