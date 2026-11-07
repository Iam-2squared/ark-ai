# ARK AI — Run677: privacy early-veto CI repair and Planner callback provenance

**Scope:** FREE-ONLY, NON-UI, disconnected/mock-only. Draft PR #8 (`research/jarvis-foundations`). Report prepared from GitHub source/CI observations on 2026-11-07 JST; administrative time is not authenticated audit time or consent.

## Package 1 — repair inherited CI failure without relaxing privacy checks

- Incoming exact PR #8 HEAD: `e4502cebbf909cd873da7e77effecc551adb6a0c`. [CI #42332080755](https://github.com/Iam-2squared/ark-ai/actions/runs/42332080755) completed **FAIL 6/6**. GitHub job logs on Ubuntu Python 3.11 and Windows Python 3.13 show **nine** failing parameterizations in `tests/test_retention_recheck_postdenial_epoch_run537.py` at line 97; all expected four private inventory reads, but observed zero.
- Run676 had *intentionally* added an import-time class-lookup-hook check to `src/ark/personal_context_retention_recheck_review.py`. A replaced `SyntheticRetentionRecheck.__getattribute__` is now rejected **before any private SQLite projection**. The older test's assumption that the substituted last-getter hook runs after four reads was obsolete, not evidence that source guards should be relaxed.
- Test-only commit `e61eb70d61ad79b0edd1a584fad6c46166b8c58a` updates all nine parameterizations to require **zero** private inventory reads and **zero** malicious getter invocations, unchanged cached item/scope/store paths, and the existing `SyntheticRetentionRecheckRejected` error. Unmodified positive control still requires an inert, content-free result.
- No production privacy code or frozen tests were weakened by this repair. The latest-head cross-platform PASS is **not yet established**.

## Package 2 — bind multi-step synthetic Planner to its original receipt-review callback

- Source commit `deed2eae4ec2d02a0bcfc746ee318ef9061f592f`; format-only Ruff line-wrap `f22c0ead47466caaa70785cee16be4cab8fe3eeb`; new negative/regression test commit `004b4960fba08a05e25d474430759bb3ec1fa928`.
- `src/ark/agency/disconnected_planner_success_bundle_review.py` now captures the imported `single.review_synthetic_succeeded_read_correlation` function at module import and refuses a substituted callback **before** accepting a synthetic multi-step evidence bundle. Class/denial/step/pair snapshots are preserved.
- `tests/test_planner_succeeded_read_bundle_run676.py` adds a regression where an injected callback would otherwise fabricate or interrupt the detached receipt join; it must remain uncalled. After restoring the original function, the normal local two-step fixture must still produce only a non-authorizing correlation receipt with **zero backend invocations**.
- There is **no external ToolBackend execution**, no WRITE authorization, no implicit retry, and no change to the normal Planner SUCCEEDED/UNKNOWN/WRITE recovery veto. These fixtures do not independently authenticate a historical READ result.

## Separate read-only integration / V3 gate audit (no source or frozen evidence changes)

- Confirmed from `src/ark/agency/synthetic_mock_action_cycle_review.py`, `durable_occurrence_review.py`, `synthetic_occurrence_audit_link_review.py`, `registry.py`, `policy.py`, and `audit.py`: synthetic Planner RUNNING, occurrence reservation, pre-action audit, and optional audit-link are **separate local SQLite commits**, not one globally atomic transaction. Injected interruptions must leave a non-replayable UNKNOWN WRITE, and synthetic receipts' authority flags remain false. The in-memory `PermissionGate` token-consumption set is **not** durable user authentication. Actual exactly-once effects and trusted-clock authorization remain blocked.
- [V3 pre-paid compute gate](https://github.com/Iam-2squared/ark-ai/blob/805b377697472268db02650a89c7a94b1c5337c8/docs/v3/PRE_PAID_COMPUTE_GATE.md) was re-read: immutable base/tokenizer and converter byte identities, approved provenance/rights/contamination decisions for 120/30 examples, pinned environment and hardware, user-approved JPY/timeout ceilings, and final branch CI remain prerequisites. **No payment, external compute, model training, Candidate generation, protected V2 evaluation, or promotion** occurred.

## Exact CI evidence and limitations

- Baseline Run676 HEAD `e4502cebbf909cd873da7e77effecc551adb6a0c`: [#42332080755](https://github.com/Iam-2squared/ark-ai/actions/runs/42332080755) **COMPLETED FAIL 6/6**, 9 identifiable inherited pre-access fixture expectation failures. This failure is preserved, not relabeled.
- Current Planner-source-and-test HEAD `004b4960fba08a05e25d474430759bb3ec1fa928`: [#42335300129](https://github.com/Iam-2squared/ark-ai/actions/runs/42335300129) **IN PROGRESS 6/6** when sampled; latest exact-head **GREEN is NOT VERIFIED**, and the new callback test is not yet claimed PASS.
- A later report/checkpoint commit will have a distinct HEAD and automatically triggered CI; no equivalence is assumed. No duplicate workflow was manually dispatched.
- Frozen V1/V2/Local UI/Launcher contracts/evidence, main, V3 Draft PR #5, paused UI Draft PR #9, and all training/evaluation gates were untouched. Overall ARK/JARVIS remains **NOT_PASSED**.

## Dependency-aware next work

1. Inspect exact-head six-job CI. If the early-veto regression or imported callback pin fails, repair through **normal GitHub Contents writes only**; keep unrelated workstreams separate while CI runs.
2. Extend Planner cross-step retained READ evidence with immutable provenance and reentrancy checks, but do **not** let local synthetic receipts authorize normal SUCCEEDED recovery.
3. Continue Memory COMMIT-UNKNOWN nonattribution, CAS/ABA/expiry/WAL coherent snapshots and privacy retention/revocation safety, followed by disconnected-only Registry/PermissionGate/occurrence/audit integration.
4. A real authorized action would need independently trusted time, human authorization, durable exactly-once occurrence claims and a defensible cross-store crash protocol. Keep these as **blocked architecture gates**, not asserted accomplishments.


## CI follow-up after source-and-test run

- [CI #42335300129](https://github.com/Iam-2squared/ark-ai/actions/runs/42335300129) Ubuntu Python 3.11 **COMPLETED FAIL**: **10,209 PASS, one SKIP, one FAIL** at `tests/test_planner_succeeded_read_bundle_run676.py::test_replaced_bundle_authority_carrier_rejected_before_read_review`. The test expected the established contiguous diagnostic `carrier changed`, but the new combined text was `bundle output carrier or callback changed`.
- The source's **error string only** was corrected in `f6159a0b65e9b5d80fb415d842b03a3dc06e2753` to `bundle output carrier changed or callback changed`, retaining compatibility with the existing carrier test and new callback test while leaving both the callback identity check and deny-only logic unchanged. This is not a safety-gate relaxation.
- Remaining jobs and the corrected exact-HEAD CI were not considered PASS before completing. Historical failure remains recorded.
