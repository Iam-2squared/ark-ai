# ARK AI — Canonical Project Status

**LATEST — Run645 / 2026-11-06 JST: four non-UI work packages saved, 25 new test cases and an actual receipt-field/constructor pre-access source hardening. Latest exact-head six-job CI is IN PROGRESS / NOT YET GREEN. ARK/JARVIS/V3 = NOT_PASSED. UI DEVELOPMENT PAUSED.**

**Saved at:** **2026-11-06T08:52:34.750+09:00 Asia/Tokyo/JST** (runtime UTC sample immediately before an ordinary GitHub Contents write; not a trusted action clock, independent runtime identity, or human approval).

## LATEST — branch, work basis and checkpoint authority

- Branch: research/jarvis-foundations; [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8), OPEN, unmerged.
- Invocation work-basis HEAD: cae73a433f70dd0a5d8873a2f6c74407a45f1723 (Run644 checkpoint; 6/6 previous CI GREEN).
- Source/test work-result HEAD: e5f8dc79ad8e5b913dfd21dff7a6a754afff9d6d (Run645 fourth package).
- Checkpoint write-basis HEAD: f323c0d6de796950186fd9a08f775c545d22ad0e (all new source/tests and Run645 report already saved; freshly re-read before this write).
- Checkpoint-result HEAD: GitHub allocates the new commit SHA after this Contents API write. Do not confuse this write-basis SHA with the result; see Contents update response and subsequently re-read PR head. Existing checkpoint blob SHA before write: 74bc9814f826f945febe8e7ea38f07b9201f6111.
- [Run645 technical report and precise evidence](https://github.com/Iam-2squared/ark-ai/blob/f323c0d6de796950186fd9a08f775c545d22ad0e/docs/JARVIS_RUN645_NON_UI_MEMORY_PLANNER_RESERVATION_RECEIPT_CUSTODY.md).
- [Run644 prior canonical status](https://github.com/Iam-2squared/ark-ai/blob/cae73a433f70dd0a5d8873a2f6c74407a45f1723/docs/PROJECT_STATUS.md). Full Run639 historical status archive retained in docs/status_archive/PROJECT_STATUS_THROUGH_RUN639_PART1.md and PART2.md. Git history and frozen evidence retained.

## NEW work this invocation

1. Memory two-handle generation-CAS ambiguity: test commit 19b63150e8f9050a73e46d1b6aa3e33a9488a628, tests/test_memory_two_handle_ambiguity_recovery_run645.py, **4 authored cases**. Competing writer token must admit one committed update; cold manual review cannot attribute the author or enable retry. Divergent/two-update histories must not be mistaken for a caller's exactly-once commit. No Memory DDL/schema change.
2. Planner independent root concurrency and recovery: test commit baf5f4fa46c2eb9393323d406b9cb52c3648cf46, tests/test_planner_parallel_independent_recovery_run645.py, **3 authored cases**. Distinct roots can both start; a failed/cancelled root blocks only its dependent child. Other RUNNING state remains UNKNOWN/non-replayable at restart. No real tool backend.
3. Memory retained event prefix lifecycle: test commit 12d051aa047069b8a922a03d8b8b69f2f7ede6bf, tests/test_memory_event_prefix_lifecycle_run645.py, **3 authored cases**. Interior append-only ID gap fails closed; valid delete/recreate same identity is a new local lifecycle, not authenticated actor or permission.
4. Durable synthetic WRITE reservation receipt: source commit 0a0f28434b60681259843a657b014446f5b2faa6 in src/ark/agency/durable_occurrence_review.py plus test commit e5f8dc79ad8e5b913dfd21dff7a6a754afff9d6d in tests/test_occurrence_receipt_preaccess_slots_run645.py, **15 authored cases**. Import-time identity checks now cover five slotted field descriptors and constructor/getter hooks, not just three False-only properties and the class alias. Poisoned descriptor must be rejected before executing even after local COMMIT; spent one-shot remains spent. All checks remain synthetic/disconnected.
5. Technical evidence document f323c0d6de796950186fd9a08f775c545d22ad0e. **25 new regression cases authored, NOT a pytest PASS count.** No paid/external compute or real action.

## CI / tests / evidence at checkpoint read

- Inherited Run644 exact HEAD cae73a433f70dd0a5d8873a2f6c74407a45f1723: [Actions #42125020030](https://github.com/Iam-2squared/ark-ai/actions/runs/42125020030), **6/6 GREEN**.
- [Package A #42131268810](https://github.com/Iam-2squared/ark-ai/actions/runs/42131268810): **4 GREEN / 2 IN PROGRESS** (zero observed failures).
- [Package B #42131347135](https://github.com/Iam-2squared/ark-ai/actions/runs/42131347135): **4 GREEN / 2 IN PROGRESS** (zero observed failures).
- [Package C #42131479565](https://github.com/Iam-2squared/ark-ai/actions/runs/42131479565): **3 GREEN / 3 IN PROGRESS** (zero observed failures).
- [Source hardening #42131696145](https://github.com/Iam-2squared/ark-ai/actions/runs/42131696145): **3 GREEN / 3 IN PROGRESS** (zero observed failures).
- [Source plus new receipt tests #42131851035](https://github.com/Iam-2squared/ark-ai/actions/runs/42131851035): **3 GREEN / 3 IN PROGRESS** (zero observed failures).
- [Technical report HEAD #42132098564](https://github.com/Iam-2squared/ark-ai/actions/runs/42132098564): **0 GREEN / 6 IN PROGRESS** at last job read.
- The new checkpoint commit itself may trigger a distinct workflow. No duplicate equivalent workflows manually dispatched. Latest-head 6/6 GREEN **NOT VERIFIED**; repair only actual future failure logs.
- Local git ls-remote failed because github.com DNS could not be resolved in the local container. No local pytest/Ruff/real-PC run is asserted.
- Local synthetic history and receipts cannot prove external exactly-once, physical identity/consent, cross-database atomicity, trusted clock, real backend success, or permission for action. Unknown WRITE outcomes must not be automatically retried.

## Frozen branches, authorization and costs

- main verified unchanged at 7a843f17eb96ed13d66f23b58b06406b3002e405.
- [Draft PR #5](https://github.com/Iam-2squared/ark-ai/pull/5) verified OPEN/Draft/unmerged at 805b377697472268db02650a89c7a94b1c5337c8; no Contract 1, dataset identity, frozen V2 final evaluation or paid GPU work.
- [Draft PR #9](https://github.com/Iam-2squared/ark-ai/pull/9) verified OPEN/Draft/unmerged at 3b49048dd70eebcb6268299b9ecef4e301bbc0fd; ALL UI/frontend development paused, its branch untouched.
- Frozen V1/V2/Local UI/Launcher contracts/evidence unchanged. No new paid service/API, external GPU, real Candidate/adapter generation, promotion, credentials, material irreversible changes, physical-PC actuation, real backend, protected evaluation opening or main merge.

## Next plan / 今後の方針

1. Determine the exact HEAD's all-six CI outcome; on any FAIL inspect job logs and fix the smallest source/test issue through the ordinary safeguarded Contents path. Never mislabel an older or in-progress HEAD as GREEN.
2. Memory: COMMIT-UNKNOWN triage, event/row coherent prefix, CAS and expiry under separate SQLite writers; keep retained evidence detached and never infer actor/consent from hashes.
3. Planner: persistent UNKNOWN and terminal/dependency cascade recovery with competing handles and process restart; no automatic WRITE replay.
4. After exact-head GREEN, develop isolated mock-only ToolRegistry/PermissionGate and durable one-shot reservation/audit-before-action integration, preserving trusted-clock and occurrence identity boundaries.
5. Independently strengthen privacy-safe Personal Context, proactive scheduler/readiness and observation/multimodal fixture contracts; audit free-only V3 path/identity guards. No UI lane.
