# ARK AI — Run647 non-UI retained-carrier pre-access integrity

**Scope:** isolated, reversible JARVIS-core foundation hardening in Draft PR #8. No frontend/UI, ToolBackend dispatch, real execution, privileged evaluation, Candidate, paid compute, trusted clock assertion, or real-model work. ARK/JARVIS overall **NOT_PASSED**.

**Work-basis HEAD:** `56c28125e391f0c40a190cfb859a3b1b2c4be1b5` (Run646 checkpoint, [CI #42140329053](https://github.com/Iam-2squared/ark-ai/actions/runs/42140329053), **GREEN 6/6**). This evidence was verified through all six actual GitHub Actions jobs before this run's changes.

## Package A — durable WRITE restart report carrier

- Source `src/ark/agency/disconnected_write_restart_binding.py` at `45e23dfbfa4fde764d1b506e79e5aeba94be5997`.
- The existing `OfflineWriteRestartReport` constructor identity check now also pins all five dataclass field descriptors and three lookup hooks from import time, before inspecting the independent SQLite reservation ledger. A preinstalled substituted descriptor may not execute even when all deny-only properties still return False.
- `tests/test_write_restart_report_slots_run647.py` at `c47e24ea30b2e3773fc89071334a0835818de6b7`: **9 authored cases** for five slots, two lookup hooks, a reentrant quarantine callback replacing a field, and a valid UNKNOWN WRITE remaining manual-only.
- The SQLite ledger cannot attest external effects, consent, cross-store atomicity, or a right to replay.

## Package B — retained Memory row/event comparison input/result carriers

- Source `src/ark/memory/sqlite_retained_row_delta_review.py` at `d74baa926a85a2ea0e608d1b53fa8a731b226c2e`.
- Import-time exact identities now bind the four fields and constructor/lookup hooks of `MemoryRowDeltaWitness` and the five fields/hooks of `MemoryRowDeltaReview`. Capture and comparison reject class-level executable replacements before the first private SQLite scan, also rechecking after callback boundaries.
- `tests/test_memory_row_delta_carrier_preaccess_run647.py` at `1d3c6c85c767c975b8940af46bf2fdd854e66caf`: **15 authored cases**, including a post-scan callback poison and legitimate unrelated event append; no Memory plaintext is included in witnesses or the report.
- Row/event hashes are local consistency evidence only, not authenticated writer provenance, policy approval, independent custody, or secure-erasure proof. Existing frozen Memory v1 DDL is unchanged.

## Package C — proactive disconnected scheduler resume result

- Source `src/ark/offline_schedule_resume_review.py` at `9641f6729e2c1cda8c15d088a11e06f8ee02e022`.
- `OfflineScheduleResumeReview` now pins its six result slots and three lookup hooks before reading the quarantined SQLite history or evaluating recurrence fields; rechecks at the existing `stable()` callback boundary. Existing denial properties and passive restart semantics remain unchanged.
- `tests/test_schedule_resume_result_slots_run647.py` at `49e85165dd7e88530d995b17e08a027f3613ae48`: **10 authored cases**, covering six field poisons, two lookup hooks, late callback mutation and valid deny-only due preview.
- The scheduler cannot start a timer, notify, dispatch tools or prove caller time/consent.

## Change review and validation limits

- Compare `56c28125e391f0c40a190cfb859a3b1b2c4be1b5...49e85165dd7e88530d995b17e08a027f3613ae48` via GitHub: **6 sequential commits**, three modified backend source files, three new backend test files. No other changed paths; no frozen contract/UI changes.
- **34 new authored regression cases** (9+15+10): authored case count, **NOT** a pytest PASS or review approval count.
- Work-basis [#42140329053](https://github.com/Iam-2squared/ark-ai/actions/runs/42140329053): Ubuntu/Windows Python 3.11, 3.12, 3.13, **6/6 GREEN**.
- Source A [#42146467516](https://github.com/Iam-2squared/ark-ai/actions/runs/42146467516): **completed GREEN** at last read; other six-matrix runs are not assumed GREEN while pending.
- Package A tests [#42146580223](https://github.com/Iam-2squared/ark-ai/actions/runs/42146580223), package B tests [#42147056336](https://github.com/Iam-2squared/ark-ai/actions/runs/42147056336): Ubuntu **3/3 GREEN**, Windows **IN PROGRESS** at last job read.
- Latest source-plus-test HEAD `49e85165dd7e88530d995b17e08a027f3613ae48`: [#42147281552](https://github.com/Iam-2squared/ark-ai/actions/runs/42147281552), **IN PROGRESS** at report authoring. Do not present latest six-job PASS without job evidence.
- No local Ruff/pytest or unavailable physical-PC test was performed; PR checks are the validation gate. These are Python in-process class-descriptor defenses, not a general sandbox against a malicious interpreter.

## Required follow-up

1. Verify **latest exact-head** GitHub Actions matrix 6/6; if a failure exists, review exact job logs and use only normal safeguarded Contents API for semantics-preserving repairs, then independently inspect subsequent CI.
2. Keep Memory COMMIT-UNKNOWN, retained row/event continuity and cross-process coherent-snapshot evidence as highest-impact independent backend lanes.
3. Advance disconnected Planner UNKNOWN/terminal recovery, audit-before-mock reservation, registry-bound identity and durable occurrence replay constraints after dependency GREEN.
4. Preserve frozen V1/V2/Local UI/Launcher evidence. Keep PR #5 and PR #9 Draft/unmerged; UI work paused, no paid/external compute, protected V2 final evaluation, irreversible operations or main merge without separate authorization.

## CI forensic addendum — actual Run647 test failure and repair

- The first combined source/tests CI [#42147281552](https://github.com/Iam-2squared/ark-ai/actions/runs/42147281552) failed on Ubuntu Python 3.11/3.12/3.13: Python 3.11 log recorded **5 FAILED, 9,305 PASSED, 1 SKIPPED**. All five were existing schedule-resume tests expecting the previous error diagnostic `denial descriptor replaced`, while the new preflight check correctly rejected earlier with `offline resume result carrier changed`. This is an **asserted exception message mismatch**, not evidence of an authorized dispatch, failed safety rejection, or a successful latest matrix. Exact failed tests: two parameterizations in `tests/test_schedule_resume_class_binding_run573.py` and three in `tests/test_schedule_resume_constructor_static_denials_run621.py`.
- Minimal semantics-preserving source repair: `c5841bd8894237004bc509a078a1bec9a0714047`. The guard still rejects at the earliest point, before inspection; its error message now includes **both** `result carrier changed` and `denial descriptor replaced` to preserve previous regression diagnostics and the new strict pre-access cases. No test expectations or deny-only properties were relaxed.
- The repair starts its own GitHub PR CI; **6/6 exact-head GREEN requires new actual job evidence**. Do not equate a queued run or earlier GREEN with verification of this patched HEAD.
