# Run604 — Non-UI retained Memory and manual WRITE triage descriptor custody

Work basis: Draft PR #8 `research/jarvis-foundations`, `f5072003256738c16bd6df579235517cae437daf` (Run603 checkpoint). This is a non-normative, reversible, offline-only safety regression note. Source/test writes were made by the standard GitHub Contents API, without force push or a raw-Git bypass.

## Three independent work packages

1. **Memory generation retained CAS verification:** `src/ark/memory/retained_generation_fence.py`, commit `61cc802692600dbb5c11146104abdfd834aca6c4`, pins `MemoryGenerationReview`'s three original False-only class descriptors at import time, checks the raw class dictionary before any getter, and rechecks across the readback boundary. `tests/test_memory_generation_original_denials_run604.py`, commit `4ae1e21b58eb5f33c8d1f2aaa7666e7f4ffd8c0c`: **7 authored pytest parameter-expanded cases** (three flags x two injection moments and one unchanged successful reconciliation). These regressions require zero hostile descriptor invocations; CI, not an asserted local run, determines whether they PASS.

2. **Retained coherent Memory epoch comparison:** `src/ark/memory/retained_epoch_review.py`, commit `2a3321f15057523b4839bf2632bd03490434046e`, statically pins five imported `AtomicMemoryEpochReview` denial definitions and five comparison-result denial definitions. The previous epoch and current epoch never prove writer/clock/consent custody. `tests/test_memory_retained_epoch_original_denials_run604.py`, commit `431752e81d77103b8276e0beaec4ca70015b6d33`: **11 authored cases** (five input-property substitutions, five output-construction substitutions, one ordinary unchanged-epoch comparison). Its original Ruff I001 import ordering was corrected without changing assertions at `62d4cfaaacd147dd19a6a32c37a092d93866868d`.

3. **Manual-only synthetic WRITE triage verification:** `src/ark/agency/offline_write_triage_verify.py`, commit `58acc3bf207d7579df00d5cc95568679ebf157c4`, checks original four packet, five result and one witness denial-property descriptors before validating a detached checklist, before any False-only getters, and at later stable result boundaries. `tests/test_offline_write_triage_original_denials_run604.py`, commit `2d0199b2d4ffd6597251dc125d542e5be2392af8`: **11 authored cases** (four packet flags, one retained witness, five late result flags and one clean checklist). Ruff I001 import ordering corrected at `d1f35c3546baf4c14ef0b05566ebf89518d98f68`, preserving the test semantics.

**Total: 29 authored regression cases, not 29 independently locally executed PASS.** No production schema, frozen contract, runtime backend, PermissionGate policy or live ToolBackend path was edited.

## CI findings and limits

- Previous checkpoint `f5072003256738c16bd6df579235517cae437daf`: [#41811596941](https://github.com/Iam-2squared/ark-ai/actions/runs/41811596941) **6/6 completed-success** (Ubuntu and Windows; Python 3.11/3.12/3.13), confirmed on this invocation before new changes.
- Intermediate commits `431752e8`, `58acc3bf` and `2d0199b2` encountered real [#41816270276](https://github.com/Iam-2squared/ark-ai/actions/runs/41816270276), [#41816408090](https://github.com/Iam-2squared/ark-ai/actions/runs/41816408090), [#41816514948](https://github.com/Iam-2squared/ark-ai/actions/runs/41816514948) Ruff **I001** failures. Logs identified only import placement of `ark.memory.retained_epoch_review` and `ark.agency.offline_write_triage_verify` in the two new tests. Both were re-ordered using the exact Ruff suggestion. Safety predicates were not weakened.
- Post-fix test HEAD `d1f35c3546baf4c14ef0b05566ebf89518d98f68` [#41816720424](https://github.com/Iam-2squared/ark-ai/actions/runs/41816720424) was **IN PROGRESS** at its last observation, not asserted 6/6 GREEN. Later documentation and checkpoint commits require their own exact-HEAD result check.

## Frozen and authorization boundaries

Frozen Memory `src/ark/memory/contracts.py` blob `b6e93821ecd69270a7634aceb20775dc36e9953c`, V3 PR #5 `docs/v3/CONTRACT.md` blob `b44f7b0e7e619c225ab662ed9c1fc8deae2b1e23`. V1/V2/Local UI/Launcher evidence unchanged. PR #5 is Draft/unmerged; PR #9 is Draft/unmerged and UI PAUSED. No new UI/frontend modifications.

Class descriptor identity is a local static defense, not proof against arbitrary hostile Python process mutation, consent, trusted timestamps, witness origin or storage custody. SQLite snapshots/hashes are not a restart-safe authorization issuer or real-world exactly-once effects. All WRITE triage remains **manual-only and nonexecuting**. No paid services, external GPUs, credentials, camera/mic, live backend, physical PC, Candidate, protected evaluation, approval-required merge or destructive operation.

## Next integration sequence

1. Verify six CI jobs on the exact post-fix and final checkpoint HEADs; diagnose any pytest failures from actual job logs. Do not count early I001-limited runs as test PASS.
2. Advance Memory COMMIT-UNKNOWN coherent readback and Planner mixed FAILED/BLOCKED/UNKNOWN restart without replay.
3. Keep ToolRegistry, exact-type PermissionGate, durable occurrence, audit-before-mock-action and startup readiness integration isolated until dependent exact-HEAD tests are GREEN.
4. Preserve V3's explicit preflight and full-training authorization stops and the November 3 UI pause.
