# Run654 — Non-UI Personal Context restart and Observation lineage custody

**Scope:** Draft PR #8, `research/jarvis-foundations`, non-UI, reversible local/offline groundwork only. Initial exact work basis: `8a3bfb4a4b59ff2fe5b73c6be67dc86f985e3437`. No UI, production ToolBackend, sensor, paid API, compute, Candidate, protected V2 evaluation, contract changes or main merge.

## Package 1 — Personal Context restart witness (source + 17 test cases)

- `src/ark/personal_context_replay_recovery.py` now delegates retained and observed witness validation to the **existing ledger's** `_check_witness`. That verifier checks import-original exact slotted `count` and `chain_sha256`, constructor/allocation/lookup hooks, bounded scalar shape and the original non-authorizing witness getter **before reading any witness metadata**. The recovery API retains its own exact `OfflineContextRecoveryRejected` exception for rejected witness values.
- Previously, recovery's private `_witness_fields` only pinned `independent_custody_proven`, so a patched `count`/digest descriptor or lookup hook could execute before the later rejection. This was a local Python class-mutation exposure, **not** evidence of a real compromised user or external attack.
- `tests/test_context_recovery_witness_preaccess_run654.py` contributes **17 authored tests**: 5 direct pre-access poison scenarios, 5 before-SQLite scenarios, 5 reentrant-after-observed scenarios, 1 isolated child-interpreter `__new__` poison case, and 1 healthy read-only restart. Inherited CPython allocation slots are never poisoned inside the parent pytest interpreter.
- No context text is stored or read and no consent, independent custody, or automatic replay is granted. COMMIT-UNKNOWN still requires explicit reconciliation rather than a blind retry.

## Package 2 — Observation lineage review result custody (source + 16 test cases)

- `src/ark/observation_lineage_review.py` pins import-original exact `SyntheticObservationLineageWitness` class identity, 4 slotted result fields, 4 constructor/allocation/lookup hooks and 3 denied capture/disclosure/dispatch properties. The guard runs before local observation-window processing, immediately before/after result construction, and around late authority callbacks.
- A counterfeit False-only result getter is executable Python, not an authority denial. Rejecting its definition before invocation is stronger than checking only the value that it returns. The lineage digest remains local diagnostic integrity evidence; it authenticates neither the media source nor a human decision.
- `tests/test_observation_lineage_original_carrier_run654.py` contributes **16 authored cases**: 10 preinstalled result hook poison cases, 4 late JSON serialization hook cases, 1 child-interpreter inherited-`__new__` case and 1 healthy deterministic denial-only result.
- Two earlier lineage test files (`run419`, `run525`) were updated to assert early safe refusal rather than expect an injected malicious False getter or forged constructor to execute twice. **No production safety checks were relaxed.**
- No real camera, microphone, screen, network, media collection, notification, user data export or ToolBackend operation.

## Package 3 — Planner diamond recovery (3 regression cases)

- `tests/test_planner_diamond_cross_handle_terminal_run654.py` adds **3 authored cases** for two independent handles concurrently starting two roots of a shared diamond DAG. Root A FAILED or CANCELLED propagates BLOCKED through join and tail once, while root B may independently SUCCEED. After reopening the SQLite journal, revisions and the retained high-water witness remain stable, the failed step/blocked join cannot be retried, and the unaffected independent branch can proceed without treating another RUNNING as safely dispatchable.
- A separate success-path regression requires **both roots** to durably SUCCEED before the join can enter RUNNING, then verifies restart classifies the join as ambiguous/UNKNOWN, not automatically executable.
- This package only exercises established source contracts using ephemeral SQLite; no executable source changes or real tools.

## Package 4 — Proactive attention input carrier custody (22 regression cases)

- `src/ark/proactive_attention_preview.py` now checks the **import-original field descriptors and constructor/allocation hooks** of the exact frozen `AttentionBudgetPolicy` and `SyntheticSurfaceMarker` classes, in addition to existing lookup hooks. A poisoned input slot must be rejected before inspecting synthetic scope/trigger/observation hashes; all JSON/digest callbacks are bracketed by the existing stable checks.
- `tests/test_proactive_attention_field_allocation_custody_run654.py` contributes **22 authored cases**: 13 original class slot/initializer poison cases; 6 reentrant digest-callback poison cases; 2 isolated inherited-`__new__` child-process cases; 1 healthy deny-only preview. A reviewed test expectation was corrected to `REVIEW_ONLY` at the 1ms cooldown boundary (last marker 90ms, review at 100ms), before any PASS claim.
- No clock trust, consent, notifications, scheduled execution, media capture, or automatic replay is added. This is local synthetic planning only.

## Source/CI custody

| Check | Evidence |
| --- | --- |
| Prior exact-head Run653 | [#42171987643](https://github.com/Iam-2squared/ark-ai/actions/runs/42171987643): **6/6 GREEN**, verified before Run654 work |
| Context source | `abf867d2c71039bea6c19f11dd86b4c0fb0c2bc7`, [CI #42176781657](https://github.com/Iam-2squared/ark-ai/actions/runs/42176781657) |
| Context regression | `6a0fd37e99fe780b9e15d94a1685e0d762e16e25`, [CI #42176868725](https://github.com/Iam-2squared/ark-ai/actions/runs/42176868725) |
| Observation source | `8291a2109bb6f582eeb28555bc81bbc6d29d7915`, [CI #42177130598](https://github.com/Iam-2squared/ark-ai/actions/runs/42177130598); superseded intermediate source-only CI **FAIL** on old test expectations (Ubuntu 3.11: 3 FAIL / 9,518 PASS / 1 SKIP). Existing tests expected substituted callbacks to execute. |
| Observation corrected legacy tests | `a61cf2f37b87ff38450f9fc1f7a171005c75011f`, `5c07089e0cf90b129ae59065a1305c6e20c1dc46` |
| Planner diamond regression | `f1237c0934df8f9252ecee6163f3ed4e14fb87a2`, [CI #42177947515](https://github.com/Iam-2squared/ark-ai/actions/runs/42177947515) **IN PROGRESS** at drafting |
| Attention original input guard | `f0c78f4e27677a3013503b6d9632b4a6918f50be`, [CI #42178496925](https://github.com/Iam-2squared/ark-ai/actions/runs/42178496925) **IN PROGRESS** at drafting |
| Attention corrected source/test head | `86e204a184598b6ed5e7592169ebef600d3f9592`, [CI #42178663158](https://github.com/Iam-2squared/ark-ai/actions/runs/42178663158) **QUEUED** at drafting; latest exact-head six-environment CI not yet verified GREEN |
| Observation new regressions | `d118022fc057c525f1e719fadcfd9f32fcf3aae4`, [CI #42177321918](https://github.com/Iam-2squared/ark-ai/actions/runs/42177321918) **QUEUED** at last read |

**58 authored new test cases (17 Context + 16 Observation + 3 Planner + 22 Attention) is NOT a claim of 58 measured passes.** The final corrected source/test exact-head six-environment CI is **not yet proven GREEN** at document drafting. No full local checkout/pytest is claimed: public GitHub clone DNS failed in this execution environment. All writes used GitHub's ordinary Contents API with a fresh PR HEAD check before each write; no raw object/ref bypass or force push.

## Safety boundaries and next work

- Draft PR #5 remains under V3 frozen-contract, human-review, immutable revision/hash, cost and separate authorization gates. Draft PR #9 UI branch stays untouched and frontend work remains paused. Draft PR #8 remains unmerged.
- Prioritize **final corrected exact-head six-job CI**, fix only actual failures, then independently strengthen Memory COMMIT-UNKNOWN/event coherence and Planner + immutable Registry/PermissionGate + trusted-clock audit-before-action + durable occurrence in disconnected/mocked fault-injection tests.
- Never infer success of real external actions from an SQLite receipt/hash, never auto-retry ambiguous WRITE or context requests, and never open protected V2 evaluation / paid compute without explicit authorization.
