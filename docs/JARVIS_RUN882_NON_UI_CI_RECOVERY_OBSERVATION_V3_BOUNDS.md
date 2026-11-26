# ARK AI — Run882 non-UI CI recovery and detached boundary hardening

Saved at (Asia/Tokyo/JST): **2026-11-15T07:51:19.336+09:00** (observed runtime wall clock, not a trusted time source or human approval). Branch `research/jarvis-foundations`, Draft PR #8 remains unmerged. Work-basis HEAD `09aa757d7bf3f4e76ca5cf2198bdf05b129574c6`; complete source/test HEAD `cbb53d47098b5e03279111cd882544a4ef7feaa5`. ARK/JARVIS remains **NOT_PASSED**.

## Root-cause investigation — inherited Run881 CI FAIL, not GREEN

- [Run881 checkpoint CI #43644875692](https://github.com/Iam-2squared/ark-ai/actions/runs/43644875692): all six Windows/Ubuntu matrix jobs **FAIL**. Sample Ubuntu 3.12 log: Ruff I001 import order failure in `tests/test_registry_preallocation_text_budget_run881.py`; no pytest runs on that HEAD past lint.
- Earlier [Run881 readiness source CI #43644512540](https://github.com/Iam-2squared/ark-ai/actions/runs/43644512540): six legacy transient carrier mutation cases in `test_startup_snapshot_integrity_epoch_run402.py` and `test_startup_equal_carrier_identity_run434.py` failed; original carrier epoch was pinned only *after* invoking reentrant cached `_identifier` callbacks. The callbacks could modify a snapshot before its baseline was captured.
- Normal GitHub Contents API repairs: registry import ordering commit `66a5e69fcb9fd070ee040196f82607b579830f2d` and readiness earliest-epoch capture/check-after-each-identifier commit `2cde0253b46578a2423fb7d94d41abcb88434d45`. Existing fail-closed errors and synthetic dependency semantics preserved. GREEN claims await exact-head CI; no test result invented.

## Additional independent free-only packages

1. **Observation identity ingestion:** `src/ark/observations.py` commit `66350d53cde2a56f58e048c3bc88b84177438b96`; refuse oversized exact-string source/adapter/privacy labels **before** stripping or UTF-8 allocation, retaining the 1024-byte authoritative limit and invalid UTF-8 rejection. New `tests/test_observation_preencode_label_budget_run882.py` commits `692f3e4be75209de973ceadf7acdac12504ae426` / correction `69a5a1644b01c958401962d4744afc8b91dfaf17`: 13 parametrized/single cases (oversized/ascii/multibyte/surrogate). No sensor, media acquisition, or external adapter.
2. **Detached V3 tokenizer digest:** `src/ark/v3_detached_preflight_crossbind.py` commit `d0113907b9feafba6c5c989fe36f1f3056de19dd`; direct synthetic carrier now enforces the exact 64-character digest length *before* regex, independently of the separate 4096-byte JSON packet parser. New `tests/test_v3_direct_tokenizer_digest_budget_run882.py` commit `cbb53d47098b5e03279111cd882544a4ef7feaa5`: 9 parametrized/single cases rejecting oversized/noncanonical tokenizer digest on both sides, retaining a non-authorizing positive witness.

Exactly **7 commits / 6 changed files** compared to Run881 checkpoint, confirmed by GitHub compare: three non-UI source files, one existing registry test, two new fixture tests. **22 authored cases are not 22 verified passes.** No frozen contract or evaluation data was changed.

## CI observed for specific commits (not a blanket PASS)

- [CI #43644875692](https://github.com/Iam-2squared/ark-ai/actions/runs/43644875692) 09aa757d7bf3f4e76ca5cf2198bdf05b129574c6 — FAILURE (HEAD-specific; do not infer latest PASS).
- [CI #43649875563](https://github.com/Iam-2squared/ark-ai/actions/runs/43649875563) 66a5e69fcb9fd070ee040196f82607b579830f2d — IN_PROGRESS (HEAD-specific; do not infer latest PASS).
- [CI #43649914280](https://github.com/Iam-2squared/ark-ai/actions/runs/43649914280) 2cde0253b46578a2423fb7d94d41abcb88434d45 — IN_PROGRESS (HEAD-specific; do not infer latest PASS).
- [CI #43650005906](https://github.com/Iam-2squared/ark-ai/actions/runs/43650005906) 66350d53cde2a56f58e048c3bc88b84177438b96 — IN_PROGRESS (HEAD-specific; do not infer latest PASS).
- [CI #43650053704](https://github.com/Iam-2squared/ark-ai/actions/runs/43650053704) 69a5a1644b01c958401962d4744afc8b91dfaf17 — QUEUED (HEAD-specific; do not infer latest PASS).
- [CI #43650150790](https://github.com/Iam-2squared/ark-ai/actions/runs/43650150790) cbb53d47098b5e03279111cd882544a4ef7feaa5 — QUEUED (HEAD-specific; do not infer latest PASS).

No duplicate manual workflow launches. Latest source/test HEAD `cbb53d47098b5e03279111cd882544a4ef7feaa5` has its own CI; if it is still queued or executing, no all-six GREEN claim is authorized. The technical report write and later canonical status write produce their own distinct HEADs, which must be checked separately.

## Bounds, gaps and next actions

Keep PR #5 Draft/approval-gated and PR #9 Draft/UI-paused; PR #8 Draft/unmerged; V1/V2/Local UI/Launcher frozen. Do not open protected V2 final evaluation, alter V3 training contract, generate/promote Candidate weights, run paid API/GPU, activate real ToolBackend, modify user hardware, merge main or claim trusted clock/provenance/consent. Previously observed Windows SQLite WAL/SHM unlinked-inode and multi-process Privacy Revocation races remain **unresolved** and cannot justify COMMIT-UNKNOWN replay.

1. Reconcile exact final latest-head CI and repair any failures by normal write path only; meanwhile continue other independent non-UI lanes.
2. Investigate Privacy Revocation / SQLite last-close witness races and restart verifiability without relaxing alias, link, or UNKNOWN rejection.
3. Advance Memory CAS/expiry coherent snapshots and Planner terminal/UNKNOWN recovery with independent fixtures.
4. Connect immutable ToolRegistry, exact-type PermissionGate, durable occurrence, trusted-clock-aware audit-before-action and disconnected Mock Executor only after exact-head lower-level evidence; keep all live dispatch disabled.
5. Continue privacy-safe Personal Context, proactive scheduler, observation contracts and zero-cost V3 approval/path/identity guards. **UI development remains paused.**
