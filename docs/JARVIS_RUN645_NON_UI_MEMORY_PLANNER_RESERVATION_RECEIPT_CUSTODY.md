# ARK JARVIS Run645 — Non-UI Memory, Planner, receipt custody

**Work basis:** Run644 HEAD cae73a433f70dd0a5d8873a2f6c74407a45f1723. **Run645 source/test work-result HEAD before this report:** e5f8dc79ad8e5b913dfd21dff7a6a754afff9d6d. Branch research/jarvis-foundations, Draft PR #8, unmerged. ARK/JARVIS/V3 remains NOT_PASSED.

## Package A: Memory two-handle ambiguous COMMIT

Commit 19b63150e8f9050a73e46d1b6aa3e33a9488a628; tests/test_memory_two_handle_ambiguity_recovery_run645.py; **4 new test cases**.

Two competing SQLite writers use the same retained generation-CAS token: exactly one writer should commit. A cold third reader still sees only a local matching image, NOT caller-authenticated COMMIT, consent, trusted time, or a retry grant. Different content and two subsequent matching updates must be classed as divergent, not automatically replayable. Read-only review must not alter the SQLite dump.

## Package B: Planner independent parallel recovery

Commit baf5f4fa46c2eb9393323d406b9cb52c3648cf46; tests/test_planner_parallel_independent_recovery_run645.py; **3 new test cases**.

Two journal connections independently start two roots, despite a shared independently retained genesis tail. A FAILED or CANCELLED terminal branch blocks its dependent child while an unrelated RUNNING root remains ambiguous after restart. A child cannot start before its parent succeeds. No real tools, backend or dispatch.

## Package C: Memory append-only event lifecycle

Commit 12d051aa047069b8a922a03d8b8b69f2f7ede6bf; tests/test_memory_event_prefix_lifecycle_run645.py; **3 new test cases**.

Missing interior event IDs must be rejected even when SQLite's AUTOINCREMENT high-water matches the surviving tail. Valid create/delete/recreate of the same deterministic identity produces a new local lifecycle and an advanced prefix, never author identity or permission. SQLite fixtures are disposable.

## Package D: Receipt pre-access hardening

Source commit 0a0f28434b60681259843a657b014446f5b2faa6; src/ark/agency/durable_occurrence_review.py. Regression commit e5f8dc79ad8e5b913dfd21dff7a6a754afff9d6d; tests/test_occurrence_receipt_preaccess_slots_run645.py; **15 new test cases**.

The existing synthetic reservation receipt guard originally pinned three denial-only properties and the exported class alias but not slotted field descriptors or class-local constructor/getter hooks. Frozen dataclasses can still have their class descriptors changed reflectively. The guard now compares five field descriptors and four hooks against import-time identities using vars(), before any untrusted result-field read. It also catches a forged initializer, getter or field substituted after a durable COMMIT. Existing error wording and local SQLite v1 schema stay unchanged. A post-COMMIT refusal does NOT restore an already-spent fixture reservation. New tests inject changes before a reservation or just after its committed SQLite transition, require zero injected callback executions, and verify 0 vs 1 persisted reservation respectively. The mock backend is never called.

This is synthetic fixture protection only; it does not authenticate real consent, clock, external tool outcomes or cross-database exactly-once semantics.

## CI / verification

- Inherited Run644 HEAD cae73a433f70dd0a5d8873a2f6c74407a45f1723: [Actions #42125020030](https://github.com/Iam-2squared/ark-ai/actions/runs/42125020030) **all six jobs GREEN** at the initial Run645 job read.
- Package A: [#42131268810](https://github.com/Iam-2squared/ark-ai/actions/runs/42131268810), in progress at the initial Run645 read.
- Package B: [#42131347135](https://github.com/Iam-2squared/ark-ai/actions/runs/42131347135), in progress.
- Package C: [#42131479565](https://github.com/Iam-2squared/ark-ai/actions/runs/42131479565), in progress.
- Package D source: [#42131696145](https://github.com/Iam-2squared/ark-ai/actions/runs/42131696145), in progress.
- Package D tests: [#42131851035](https://github.com/Iam-2squared/ark-ai/actions/runs/42131851035), queued at initial read.
- **25 newly written regression cases, NOT 25 pytest PASS.** Latest exact-head six-job GREEN is not yet verified. Local Git cannot resolve github.com; no local pytest/Ruff success is claimed. GitHub Actions remains the validation route.

## Frozen controls and next plan

Main, Draft PR #5, paused UI Draft PR #9, frozen V1/V2/Local UI/Launcher evaluation evidence and V3 Contract 1 were not changed. No paid API, external GPU, real Candidate training or promotion, protected V2 evaluation, credentials, physical-PC action, real backend or main merge.

Priorities: (1) confirm exact-head GitHub CI and repair genuine failures without weakening safety; (2) Memory COMMIT-UNKNOWN and event/row ancestry with competing writers; (3) Planner UNKNOWN restart/recovery; (4) registry-bound PermissionGate plus durable one-shot/audit-before-mock integration after GREEN foundations; (5) privacy-safe Personal Context, proactive and observation backend fixtures; (6) read-only V3 free-only guards.
