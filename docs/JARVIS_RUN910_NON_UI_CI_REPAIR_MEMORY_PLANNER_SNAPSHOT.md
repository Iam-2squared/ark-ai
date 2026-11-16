# ARK Run910 — non-UI CI repair and actual SQLite snapshot isolation

Scope: **disconnected, synthetic, local-only**. No training, protected evaluation, GPU, paid service, real tool execution, physical PC, new UI, personal-data capture, Candidate promotion or main merge.

## Verified initial state and CI failure

- Initial exact PR #8 work-basis HEAD: `96dbb8fefc37a2db4d1daed521c31a78978b5089`.
- [Run909 checkpoint CI #43789492254](https://github.com/Iam-2squared/ark-ai/actions/runs/43789492254) **FAIL on all six Python matrix jobs**, specifically pytest, not Ruff. The same two previously existing tests failed on Ubuntu 3.11 and other sampled jobs:
  - `tests/test_offline_context_chunk_review_run570.py::test_mutated_record_during_join_receipt_digestion_is_rejected`: expected `epoch changed`, but the stricter guarded *child* detached index rejects the globally patched SHA dependency earlier.
  - `tests/test_offline_original_denials_run570.py::test_index_false_spoof_during_hash_callback_refused`: the test's global hashlib mutation is now refused before its callback fires.
- These failures do not justify weakening the production denial gate, turning an unknown outcome into a success, or declaring prior source/test additions GREEN.

## Work packages saved with the normal GitHub Contents API

1. **Restore meaningful late-mutation coverage without mutating shared hashlib.** [`82a290b76b2bbafaecf9712878e2b0ced85d94c3`](https://github.com/Iam-2squared/ark-ai/commit/82a290b76b2bbafaecf9712878e2b0ced85d94c3) isolates the context-join digest fault in that module only. The authentic child index retains its SHA dependency; a reflected record mutation is still expected to cause an `epoch changed` denial. [`beec6060a4fabd812bc477e2057ef294662e9d58`](https://github.com/Iam-2squared/ark-ai/commit/beec6060a4fabd812bc477e2057ef294662e9d58) injects a late index-result denial spoof at the internal inventory digest boundary without replacing global hashlib. This maintains the reentrant-denial regression's security objective.
2. **Actual Memory row/event isolation, four parametrized cases.** [`ea2819999b01d7e06f362b3ea5e720ae35733f73`](https://github.com/Iam-2squared/ark-ai/commit/ea2819999b01d7e06f362b3ea5e720ae35733f73) tests independent read-only connections DURING the writer's open transaction, after the row and event have been tentatively updated. The observer must see the old committed pair, then the complete new pair after COMMIT, for create/update/delete/expire. Actual temporary SQLite v1 store; no schema change.
3. **Actual Planner journal header/event isolation, one case.** [`9e32f6b405270acc8c24b74ea653743f8a75c7b4`](https://github.com/Iam-2squared/ark-ai/commit/9e32f6b405270acc8c24b74ea653743f8a75c7b4) tests a separate read-only Planner recovery connection during the writer's `BEGIN IMMEDIATE` journal append: readers must not see a tentative event/header update. Post-COMMIT recovery of RUNNING remains ambiguous, with both dispatch and automatic replay denied. Actual temporary SQLite v1 journal; no external effect.

**Authored test additions:** four Memory parametrizations plus one Planner case. The other two changes repair pre-existing CI regression tests, and must not be counted as newly added tests.

## CI evidence and uncertainty

- Initial verified six-job GREEN baseline: [Run908 CI #43783125874](https://github.com/Iam-2squared/ark-ai/actions/runs/43783125874) at `67f558176ba873fefa0870e943c52c77a45030ab`. It does **not** certify Run909 or Run910.
- [Run910 repair CI #43794292975](https://github.com/Iam-2squared/ark-ai/actions/runs/43794292975) and [Memory CI #43794454934](https://github.com/Iam-2squared/ark-ai/actions/runs/43794454934) were running when report authored. [Planner CI #43794653373](https://github.com/Iam-2squared/ark-ai/actions/runs/43794653373) began for the Planner test HEAD; no current-head six-job GREEN claim here.
- The newest exact checkpoint CI must be evaluated independently. Never substitute a different head's CI status for that commit, and report any confirmed failure rather than implying a PASS.

## Frozen boundaries, blockers, next

Frozen V1/V2/Local UI/Launcher contracts and evidence, V2 protected evaluation gate and Draft V3 PR #5 are unchanged. UI Draft PR #9 is untouched. PR #8 remains Draft/unmerged, as does main. No human review/permission, immutable source custody, trusted external clock, real external execution or exactly-once cross-store guarantee is inferred from these synthetic local tests.

**Unresolved:** known intermittent Windows/Ubuntu WAL/SHM last-client-close cross-process sidecar race; Planner cross-store COMMIT-UNKNOWN; Memory CAS/expiry/event continuity and independent witness custody; exact-type PermissionGate plus durable preaction and Mock READ end-to-end proof; physical offline GGUF and protected V3 gates.

**Next:** certify exact-head six-job CI; fix any regression minimally; diagnose WAL phases without relaxing alias rejection; continue Memory/Planner transactional uncertainty tests; connect disconnected registry/gate/preaction/mock layers only on verified lower-level heads. Overall **ARK/JARVIS NOT_PASSED**.
