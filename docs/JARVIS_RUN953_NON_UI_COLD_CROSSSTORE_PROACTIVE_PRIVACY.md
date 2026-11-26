# ARK AI Run953 — crash-order cross-store denials, proactive dedupe, privacy-veto cold restart

**Status:** NON-UI / disconnected / synthetic / free-only; **JARVIS NOT_PASSED**. This is a scope-limited evidence note, not approval, physical-PC evidence, independent custody, a coherent cross-store snapshot, or a promise of exactly-once external effects.

**Work basis:** Run952 checkpoint commit `a2995c0cc7a5f7e7a665dfb24178d6518b115c00`. Branch `research/jarvis-foundations`, Draft PR #8. V3 PR #5 and paused UI PR #9 remain untouched and unmerged. Frozen V1/V2/Local UI/Launcher evidence and protected V2 evaluation have not been changed.

## New code/test packages

1. **Planner and Atomic ordered abrupt-exit** — `c10745ebf4f243bcb1f11561fcfe75ae6fa59e9b`; `tests/test_disconnected_crash_planner_atomic_order_run953.py`, 2 parameterized cases. A detached interpreter durably records a synthetic Planner RUNNING step, optionally records a synthetic pre-action intent plus audit, and exits with `os._exit(37)`. After restart, recover both SQLite histories independently. The RUNNING step remains ambiguous, an independent PENDING step survives, and neither store grants dispatch or replay. A witness reconstructed from its own SQLite bytes is explicitly **not independent custody**.
2. **Proactive post-COMMIT abrupt-exit** — `3362aad910b050b6009e97ee110fb585468eff30`; `tests/test_proactive_postcommit_abrupt_exit_run953.py`, 2 parameterized cases. A detached interpreter exits before or after an inert synthetic preparation marker. On restart, the committed occurrence cannot be duplicated, an absent occurrence may be prepared locally, and receipts never authorize notification or execution.
3. **Personal Context / Memory privacy-veto ordering** — `254230199b39f01164573857d5e75df253928241`; `tests/test_context_memory_veto_crash_order_run953.py`, 2 parameterized cases. A detached interpreter records private/public Memory rows and a synthetic privacy veto in both possible orders, then exits. Cold retention inventories deny private reuse and do not claim deletion; public inventory is separate. Repeated read-only diagnostics must not edit either database.

**Total authored:** 6 parameterized tests across 3 independent non-UI test packages, with no production-core changes. All use disposable local SQLite fixtures and child Python interpreters; no actual tool backend, hardware, notification, service, Candidate, GPU or training.

## CI triage and provenance

- Previous exact checkpoint `a2995c0c`: [CI #44184422251](https://github.com/Iam-2squared/ark-ai/actions/runs/44184422251) — **GREEN, six of six** (Ubuntu/Windows × Python 3.11–3.13).
- Initial test HEAD `c10745eb`: [CI #44193901918](https://github.com/Iam-2squared/ark-ai/actions/runs/44193901918) — **FAIL, 6/6**, initial Ruff F401 unused `StepState` import before pytest.
- Second test HEAD `3362aad9`: [CI #44194021228](https://github.com/Iam-2squared/ark-ai/actions/runs/44194021228) — **FAIL, 6/6**, inherited same F401.
- Third test HEAD `25423019`: [CI #44194243651](https://github.com/Iam-2squared/ark-ai/actions/runs/44194243651) — **FAIL**, same earlier F401 remained in that snapshot.
- The smallest, semantics-preserving import fix was saved through the standard GitHub Contents API as `a8da6479131282fa4ad2839d504ce1d4e6740343`. Its [CI #44194391103](https://github.com/Iam-2squared/ark-ai/actions/runs/44194391103) was **QUEUED** at the initial check. This document does **not** claim the latest HEAD is GREEN before exact job results are inspected.

## Limits and follow-on

Local post-COMMIT state cannot prove an actual effect or external receipt. Even successful distinct local SQLite reads do not create a transaction spanning Planner, audit, Memory and privacy stores. Caller-owned clocks are not trusted; retaining a witness derived from the same store cannot establish provenance. A privacy veto is a local denial marker, not proof of erasure, global propagation, or consent.

**Next:** verify latest-head CI across six environments and correct the narrow failure if any; then advance lower-level Memory WAL/SHM CAS/expiry and Planner/registered-tool durable authorization integration under disconnected-only safety. Continue free-only V3 guard review. Do not modify paused UI or frozen contracts, merge main, execute real tools, open protected evaluation, generate Candidate weights or start billable compute.
