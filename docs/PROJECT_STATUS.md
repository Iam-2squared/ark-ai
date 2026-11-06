# ARK AI — Canonical Project Status

**LATEST — Run646 / 2026-11-06 JST:** Two independent non-UI safety work packages saved: Planner retained-tail pre-access custody and proactive schedule quarantine input custody, with **44 new authored test cases**. **Latest exact-head six-job CI IN PROGRESS / NOT VERIFIED GREEN.** ARK/JARVIS/V3 = **NOT_PASSED**. **UI DEVELOPMENT PAUSED.**

**Saved at:** **2026-11-06T09:54:30.593+09:00 Asia/Tokyo/JST**, directly sampled from runtime shortly before the ordinary GitHub Contents write. This is bookkeeping, NOT a trusted action clock, runtime attestation, human review, or execution approval.

## LATEST — branch, work basis, and checkpoint authority

- Branch: `research/jarvis-foundations`; [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8), OPEN, Draft, unmerged.
- Invocation work-basis HEAD: `0f052081701f036af57131f9c8dade954b36d401` (Run645 checkpoint; [CI #42132706849](https://github.com/Iam-2squared/ark-ai/actions/runs/42132706849), six of six GREEN).
- Planner source result HEAD: `32b9a4d8dbf11d6a7f4870603b61052e6e912290`.
- Planner test result HEAD: `5e69f90977245abd4d47914b39ab911e1c619aa5`.
- Proactive quarantine source result HEAD: `de4cc438f349232d8c77941c43abc2b305f439c7`.
- Proactive quarantine test result HEAD: `687d9f35b13b1dba3a433f9daaa6d8ba5612fefc`.
- Technical-report and source/test work-result HEAD: `39492b88b93df7df6415398579ffc0ba3124af84`.
- Checkpoint write-basis HEAD: `39492b88b93df7df6415398579ffc0ba3124af84`, freshly re-read immediately before the checkpoint write.
- **Checkpoint-result HEAD:** assigned by GitHub AFTER this Contents API update; the write-basis is NOT the checkpoint-result HEAD. Verify the resulting commit and re-read the PR head after the write. Prior canonical status blob SHA: `30e8fc0868c1e3ae35c24cdfd26dd90edd9867e4`.
- [Run646 technical report](https://github.com/Iam-2squared/ark-ai/blob/39492b88b93df7df6415398579ffc0ba3124af84/docs/JARVIS_RUN646_NON_UI_PLANNER_TAIL_SCHEDULE_QUARANTINE_INPUT_CUSTODY.md). [Previous Run645 status](https://github.com/Iam-2squared/ark-ai/blob/0f052081701f036af57131f9c8dade954b36d401/docs/PROJECT_STATUS.md); older history retained in Git and `docs/status_archive/PROJECT_STATUS_THROUGH_RUN639_PART1.md` / `PART2.md`.

## NEW work this invocation

1. **Planner journal retained-tail custody.** In `src/ark/agency/planner_journal_review.py`, import-time identity checks now pin `SyntheticPlanTail`, its five field descriptors, constructor and lookup hooks together with existing recovery-result integrity checks, before preinstalled malicious descriptors can read a retained witness or SQLite. New `tests/test_planner_tail_preaccess_custody_run646.py`: **17 authored cases** for poisoned fields/hooks on both recover and append, plus normal persistent RUNNING → UNKNOWN/non-replayable recovery. No planner real execution or authority grant.
2. **Proactive schedule overdue quarantine input custody.** In `src/ark/disconnected_schedule_quarantine_ledger.py`, exact import-time `QuarantinePolicy`/`QuarantineWitness` fields and hooks are checked before `_policy_epoch` and retained `_check_witness` read input or access SQLite. New `tests/test_schedule_quarantine_input_slots_run646.py`: **27 authored cases** of poisoned input fields/hooks on inspect/write plus valid inert quarantine receipt. Existing post-COMMIT receipt-denial behavior was not moved or weakened. No notifications, timers or ToolBackend actions.
3. Technical documentation saved at `docs/JARVIS_RUN646_NON_UI_PLANNER_TAIL_SCHEDULE_QUARANTINE_INPUT_CUSTODY.md`. Exact compare of Run645 work basis to technical-report HEAD: **five commits, five files** (two modified source modules, two new test files, one report); frozen code and UI untouched.

## CI / tests / evidence at checkpoint

- Prior Run645 checkpoint `0f052081701f036af57131f9c8dade954b36d401`: [Actions #42132706849](https://github.com/Iam-2squared/ark-ai/actions/runs/42132706849) **six of six GREEN** (Ubuntu/Windows × Python 3.11/3.12/3.13).
- Planner source `32b9a4d8dbf1`: [#42139268053](https://github.com/Iam-2squared/ark-ai/actions/runs/42139268053), **3 Ubuntu GREEN, 3 Windows IN PROGRESS** at last job read.
- Planner source plus tests `5e69f9097724`: [#42139350258](https://github.com/Iam-2squared/ark-ai/actions/runs/42139350258), **3 Ubuntu GREEN, 3 Windows IN PROGRESS** at last job read.
- Quarantine source `de4cc438f349`: [#42139537960](https://github.com/Iam-2squared/ark-ai/actions/runs/42139537960), **IN PROGRESS**; not six-job GREEN at last check.
- Quarantine source plus tests `687d9f35b13b`: [#42139613293](https://github.com/Iam-2squared/ark-ai/actions/runs/42139613293), **IN PROGRESS**; not six-job GREEN at last check.
- Report HEAD `39492b88b93d`: [#42139883981](https://github.com/Iam-2squared/ark-ai/actions/runs/42139883981), **IN PROGRESS** at last Actions read. This checkpoint may start a separate CI run; do not duplicate dispatch.
- **44 newly authored test cases, NOT a pytest PASS count.** Latest exact-head CI GREEN is **NOT VERIFIED**. No local pytest, Ruff, target-PC GGUF, real model, or external execution asserted.
- Python class/slot identity tests are local in-process fail-closed checks, not protection against an omnipotent runtime attacker or external authorization. SQLite prefix checks do not authenticate evidence custody, real-world consent, trusted clock, or exactly-once external effects.

## Frozen contracts / cost / authorization boundaries

- `main` retained at `7a843f17eb96ed13d66f23b58b06406b3002e405` in initial PR metadata; not written this invocation.
- [Draft PR #5](https://github.com/Iam-2squared/ark-ai/pull/5): OPEN/Draft/unmerged at `805b377697472268db02650a89c7a94b1c5337c8`; no protected V2 final-evaluation opening, no actual training, no Candidate, no contract change.
- [Draft PR #9](https://github.com/Iam-2squared/ark-ai/pull/9): OPEN/Draft/unmerged at `3b49048dd70eebcb6268299b9ecef4e301bbc0fd`; **all new UI/frontend work paused** and branch untouched.
- Frozen V1/V2/Local UI/Launcher evaluation/evidence unchanged. No paid API/compute, external GPU, subscription, credentials, secrets, real Candidate adapter/weights, protected evaluation, promotion, irreversible action, physical-PC use, real tool dispatch or main merge.

## Next plan / 今後の方針

1. Confirm exact latest HEAD **all six** CI jobs; if FAIL, inspect job logs and make smallest semantics-preserving fix with the standard safeguarded GitHub Contents path. Never label older or pending runs GREEN.
2. Planner: after the current source path reaches exact-head GREEN, address remaining **reentrant** tail-descriptor and callback boundary drift, terminal cascade and persistent UNKNOWN/COMMIT uncertainty without automatic WRITE replay.
3. Memory: prioritize ambiguous COMMIT outcomes, CAS under concurrent SQLite handles, coherent row/event prefixes and expiry, never inferring actor/consent from a matching row hash.
4. Continue independent, free-only mock Registry/PermissionGate/audit-before-action and durable occurrence/replay integration; improve personal-context privacy and disconnected observation readiness.
5. Keep PR #5 and #9 Draft/unmerged, never resume UI, never open protected V2 or external paid compute without explicit separate authorization.
