# ARK AI — Run662 non-UI core: due-witness custody, Memory expiry ABA, conservative Planner projection

## Scope and basis

- Initial work-basis PR #8 HEAD: `ad5d5bc3ae9244e425ed27b1458e1ab9d9848da9`. Run661 exact-head Actions [#42221625886](https://github.com/Iam-2squared/ark-ai/actions/runs/42221625886) completed **6/6 GREEN** across Ubuntu/Windows and Python 3.11–3.13.
- All changes are on `research/jarvis-foundations` in **Draft / unmerged PR #8**. They do not modify `main`, PR #5, PR #9, frozen V1/V2/Local UI/Launcher contracts or UI/frontend.
- No paid compute, external GPU/API, new accounts, training, protected evaluation, real ToolBackend, OS clock attestation, notification, actual deletion, or personal-data disclosure. Synthetic SQLite fixtures and caller-asserted time only.

## Package A — due restart witness executes no replaced field/hook

**Source** `src/ark/agency/disconnected_due_recovery_review.py`, commit `7aaf27e38a45403e80883e8792e942ad0edd2932`: before reading `DueReservationWitness.count`, `.fingerprint` or `.independent_custody_proven`, pin the import-original class, both field slot descriptors, constructor/new/getattribute/getattr hooks, and False-only denial property by static class dictionary inspection. Recheck after each witness validation. An attacker-supplied getter that returns False is still substituted executable code and must not become a trusted baseline.

**Tests:** `tests/test_due_recovery_witness_preaccess_run662.py` (9 authored cases: two slots, three in-process hooks, isolated inherited `__new__`, denial property, late first-observation slot swap, ordinary unchanged path). First draft at `0cc01c3c9bbae155c451310a27b2027aa703ae76`; original `__new__` monkeypatch polluted following tests when pytest restored an inherited allocation method. Actions [#42228173840](https://github.com/Iam-2squared/ark-ai/actions/runs/42228173840) Ubuntu 3.11 logged **94 FAIL / 9,751 PASS / 1 SKIP**, caused by test pollution, *not* a validated production grant. The risky `__new__` test is now in a separate child interpreter at `36fd129c278d4094b60dce174498f982a97717f7`, preserving the rejected behavior without global test contamination. Subsequent Actions [#42228994802](https://github.com/Iam-2squared/ark-ai/actions/runs/42228994802) Ubuntu 3.11 logged **1 FAIL / 9,849 PASS / 1 SKIP**: existing test expected the old later rejection string, now correctly intercepted earlier as `due witness carrier changed`. A single test expectation in `tests/test_due_restart_original_denial_custody_run555.py` was changed at `2e5dd72f6a4cb0a40a81eca762e037c79e080588` to accept both earlier/later fail-closed messages. **The production guard was not weakened.**

These tests are local simulation only. Detecting mutable Python class descriptors is not OS-level integrity, user authorization or independently custodied history.

## Package B — Memory expiry, ABA and deadline

**Tests:** `tests/test_memory_expiry_recreation_ambiguity_run662.py`, commit `d68a47540dcc1415494c3795104948cfbcb2005e`, 5 authored cases. Independent SQLite handles demonstrate expiry → purge → re-create with the **same deterministic memory ID and revision 1** cannot use the previous `MemoryGenerationCASToken`. Old COMMIT-UNKNOWN dual review remains a manual-only blocker; new generation observation is distinct and can perform an independently initiated local CAS without extending expiry. Exact clock cutover (149 vs 150/151 ms for expiry 150 ms) denies updates at or after deadline without an extra event. Local `memory_events` lifecycle and coherent event alignment remain inspectable. Existing frozen v1 Memory methods/schema are unchanged.

A matching local row or hash is not proof that the caller wrote it; synthetic expiry is not a trusted clock, new consent, secure erase or permission to automatically retry.

## Package C — Planner restart → disconnected false-only fence

**Source:** new `src/ark/agency/disconnected_planner_fence_projection.py`, commit `d75b169fae6dda33104f167141fa1712365a60f2`. A bounded read-only projection accepts an *already recovered* synthetic `SyntheticPlanRecovery`, the exact original `PlanStep` topology, and explicit caller-asserted `READ`/`WRITE` labels. It rejects topology drift, state-membership mismatches and missing/malformed effect labels; rewrites persisted `RUNNING` to `UNKNOWN`, then delegates to the existing detached `OfflineRecoveryFence` classification in deterministic dependency-first order. Critically, it **rejects `SUCCEEDED` statuses**, since no independently validated result SHA/receipt is provided in this adapter; fabricating a success digest would improperly bridge a provenance gap. It never calls an executor, registry or PermissionGate.

**Tests:** new `tests/test_disconnected_planner_fence_projection_run662.py`, commit `674b2796e61379ad781da217682ce496a1990c59`, 9 authored cases. Read-only independent siblings retain `READY_MOCK_ONLY` (which is *not* dispatch authorization); uncertain parent holds its descendants; failed/cancelled parent propagates terminal holds; SUCCEEDED, topology and effect/membership mismatch fail closed. No auto-replay or execution on restart.

This is a **reversible offline adapter only**. No authenticated effect classification, verified journal custody, claim provenance, registry-bound identity, real permissions, or production integration is inferred.

## CI record and unresolved evidence

- Previous exact baseline `ad5d5bc3ae9244e425ed27b1458e1ab9d9848da9`: [#42221625886](https://github.com/Iam-2squared/ark-ai/actions/runs/42221625886), **6/6 GREEN**.
- Initial due test [#42228173840](https://github.com/Iam-2squared/ark-ai/actions/runs/42228173840): Ubuntu failure (94 tests contaminated by `__new__` in-process patch), corrected by subprocess isolation at `36fd129c...`.
- After isolation [#42228994802](https://github.com/Iam-2squared/ark-ai/actions/runs/42228994802): Ubuntu 3.11 1 fail from earlier-diagnostic expectation; repaired by test-only `2e5dd72f...`.
- Memory [#42228416071](https://github.com/Iam-2squared/ark-ai/actions/runs/42228416071), Planner source [#42229401760](https://github.com/Iam-2squared/ark-ai/actions/runs/42229401760) and Planner tests [#42229605718](https://github.com/Iam-2squared/ark-ai/actions/runs/42229605718) are intermediate-head checks. Their results cannot certify later corrected HEADs. Source+test Planner Ubuntu Python 3.13 logged **9,858 PASS, 1 FAIL, 1 SKIP** due only to inherited old due-denial message expectation, now fixed.
- Final repair [#42229985516](https://github.com/Iam-2squared/ark-ai/actions/runs/42229985516) at `2e5dd72f6a4cb0a40a81eca762e037c79e080588`: **IN PROGRESS at report drafting**; use actual workflow jobs to determine GREEN/FAIL. Any later report/status commit has its own exact HEAD and CI.
- **23 authored cases** across three packages; authored case counts are *not* independently verified PASS on the final HEAD. No local full-suite pytest, real PC inference, real clock/consent/effects or autonomous tool execution is claimed.

## Next / 依存関係

1. Confirm all six exact-HEAD CI jobs after the test-only diagnostic fix, repair any real failures without source relaxation. Avoid duplicate manual workflow dispatch.
2. Memory: expand COMMIT-UNKNOWN, CAS/revision/expiry/evidence snapshots across SQLite handles and independent retained prefixes; never auto-retry ambiguous writes.
3. Planner: gate SUCCEEDED projection on separately verified result receipts, align observed effect identity to immutable ToolRegistry and exact-type PermissionGate, then audit-before-action/occurrence replay with detached mocks only.
4. Continue independent privacy-safe Personal Context, observation and proactive back-end contracts and V3 free-only identity/path/licensing audits, without touching UI or opening protected gates.
