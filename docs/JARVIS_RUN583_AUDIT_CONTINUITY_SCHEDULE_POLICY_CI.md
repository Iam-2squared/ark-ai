# Run583 — Action audit history identity, detached schedule authority, and policy CI repair

**Scope:** isolated, reversible, non-UI core work on Draft PR #8. No ToolBackend calls, external dispatch, paid/possibly billable service, GPU, user PC operation, live notification, Candidate, training, final protected evaluation, main merge, or UI/frontend change.

## Work basis and saved commits

- Invocation read-basis PR #8 HEAD: `726b3851210ba8231c04e39d015a96c63003415d` (Draft, unmerged).
- Source `src/ark/agency/audit_continuity_review.py` commit `31674af373fa2ecb4f9ade181feebd0587a7718e`. The bounded read-only audit reviewer now recomputes every historical row's deterministic request ID from its stored digest, tool, capability and scope. Shape-correct but internally inconsistent rows fail even when the tail is valid and no prior witness is supplied. This reuses the existing original v1 ToolCall canonical encoding; it is **not** writer authentication, full historical attestation or real-world execution evidence.
- Tests `tests/test_audit_continuity_request_identity_run583.py` commit `df97a2f3581ee9eee727b543a8f4acb3e9ae44a1`: seven newly authored cases (five synthetic first-row rewrite variants with a valid tail, one normal retained-prefix advance and one retained-witness corruption rejection).
- Source `src/ark/agency/disconnected_batch_schedule.py` commit `17ea8981887342778307bc5377387655ee8dac9e`. Schedule build/verify now pins the original four negative authority descriptors and constructor binding. A replaced False-only permission getter is rejected rather than accepted as original authority, including after a subsequent read-only plan verification. No parallel, backend, write or replay execution is introduced.
- Tests `tests/test_disconnected_schedule_original_denials_run583.py` commit `08515ab9a7951462659d5a602d525e25474fb162`: ten newly authored cases (four per-property build denials, four per-property verify denials, constructor replacement refusal and normal dependency-wave regression).
- CI-grounded repair `tests/test_permission_instance_shadow_run582.py` commit `ff99f07984e597cd146af3b8fa273aa34a5ade88`: four existing cases were aligned with the original implementation's **earlier and stronger** denial for a shadowed `PermissionGate.authorize`. Both READ and WRITE refuse the substituted instance method; the rejection message is `registered authorization implementation identity changed`. The actual original policy source and local one-shot spend behavior were **not weakened**.

## CI / test evidence (sampled before this document)

- Prior PR #8 exact HEAD `5590b837a3664c03bf2d9b856392d87415820837` [run #41639618730](https://github.com/Iam-2squared/ark-ai/actions/runs/41639618730) **6/6 GREEN** (Ubuntu/Windows Python 3.11–3.13); not evidence for current changes.
- Read-only audit source [run #41652232702](https://github.com/Iam-2squared/ark-ai/actions/runs/41652232702); audit tests [run #41652339873](https://github.com/Iam-2squared/ark-ai/actions/runs/41652339873): audit-test HEAD showed Ubuntu failures due to **existing** earlier policy-test expected behavior, not evidence of a new audit defect. Ubuntu Python 3.11 and 3.13 logs for that HEAD showed 4 previous policy cases failing and the remaining 7,583 passing, 1 skipped.
- Detached schedule source [run #41652604759](https://github.com/Iam-2squared/ark-ai/actions/runs/41652604759); schedule tests [run #41652719740](https://github.com/Iam-2squared/ark-ai/actions/runs/41652719740) remained in-flight at sample.
- Policy test correction [run #41653031541](https://github.com/Iam-2squared/ark-ai/actions/runs/41653031541) QUEUED at sample; only subsequent CI on its **exact HEAD** can establish GREEN for the combined code. GitHub Actions triggers occurred automatically on Contents API commits; no manual duplicate workflow was launched.
- **17 new tests are authored Python test definitions, not independently executed local pytest passes or physical-PC benchmark evidence.** This run did not invoke a local repository test runner because the remote repository cannot be cloned through the local network in this runtime. The full GitHub CI result is the next verification gate.

## Frozen evidence / safety constraints

The previously frozen v1/v2/Local UI/Launcher evidence was not edited. Unchanged PR #8 frozen Memory `src/ark/memory/contracts.py` blob `b6e93821ecd69270a7634aceb20775dc36e9953c`; Planner `src/ark/agency/contracts.py` blob `13f1bb725f9c2c783e29402ca4a6e0f86b850ef9`; PR #5 V3 `docs/v3/CONTRACT.md` blob `b44f7b0e7e619c225ab662ed9c1fc8deae2b1e23`. PR #5, PR #8, PR #9 remain Draft/unmerged, PR #9 UI branch untouched, main unchanged. None of these local checks authenticates a human, grants spending, validates a trusted clock, establishes consent or permits automatic replay of UNKNOWN external effects. **ARK/JARVIS/V3 NOT_PASSED.**

## Next / 今後の方針

1. Confirm final exact-head CI 6/6 (or inspect actual failure logs and make the smallest safe correction), without repeated workflow launches or treating older GREEN as current evidence.
2. Prioritize durable registry-bound permission and audit-before-action sequence, restart-safe occurrence/replay custody, Planner FAILED/BLOCKED persistence, and Memory CAS/expiry/unknown-COMMIT reconciliation.
3. Continue disconnected Personal Context retention/withdrawal, Proactive Scheduler restart duplication control and observation fixtures without new UI, real execution, paid infrastructure, frozen contract edits or main merges.
