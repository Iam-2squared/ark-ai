# Run763 — Non-UI inert atomic recovery quarantine and input carrier preflight

Date: 2026-11-10 JST. Branch `research/jarvis-foundations`, [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8). This is a **non-normative, free-only engineering record**, NOT evidence of a completed ARK/JARVIS gate or a live execution authorization.

**Initial work-basis HEAD:** `46eaf65b45677cb7f4831dd334eaff2ba0de62a9` (Run762 report head, [CI #42803612314](https://github.com/Iam-2squared/ark-ai/actions/runs/42803612314) completed **6/6 GREEN** on that exact SHA). This older evidence does not establish Run763 test PASS.

## NEW — two isolated source/test packages, 24 parametrized test cases

### A. Read-only registered recovery quarantine

- Source: [`disconnected_atomic_recovery_quarantine.py`](https://github.com/Iam-2squared/ark-ai/blob/49936958a7ed0999d3f568e5f8e5d96329b0c26e/src/ark/agency/disconnected_atomic_recovery_quarantine.py), source commit `49936958a7ed0999d3f568e5f8e5d96329b0c26e`.
- Tests: [`test_atomic_recovery_quarantine_run763.py`](https://github.com/Iam-2squared/ark-ai/blob/4b5eccf68a709cb6ab81e100c1ab239b073ffaf8/tests/test_atomic_recovery_quarantine_run763.py), test commit `4b5eccf68a709cb6ab81e100c1ab239b073ffaf8`; **8 cases**.
- `review_registered_atomic_recovery` derives only an inert registry-bound WRITE claim, then reads the caller-retained SQLite pre-action witness and detects exact local occurrence membership. Missing, stale, malformed, changed-authority, READ or noncanonical inputs fail closed.
- The result *always* has `manual_review_required=True`, and `binding_proven=False`, `tool_dispatch_authorized=False`, `automatic_replay_authorized=False`, `external_effect_proven=False`, `independent_custody_proven=False`. No `execute()` and no backend invocation.
- **Critical limitation:** `DisconnectedAtomicPreactionLedger.inspect()` projects ONLY occurrence IDs, not persisted bound-action/request digests. Even when the same occurrence ID appears in the store under a **different** registered call, membership remains a local fact, NOT evidence of matching binding. The test explicitly locks in the denial result rather than claiming a verified binding. A later reviewed exact-row read-only comparison should be designed before considering any higher-level integration.

### B. Isolated import-original atomic input preflight

- Source: [`disconnected_atomic_input_review.py`](https://github.com/Iam-2squared/ark-ai/blob/5562fff72fb3e6d57853cac11075020c295c995d/src/ark/agency/disconnected_atomic_input_review.py), commit `5562fff72fb3e6d57853cac11075020c295c995d`.
- Tests: [`test_atomic_input_carrier_custody_run763.py`](https://github.com/Iam-2squared/ark-ai/blob/eefb507513d4ab5e897340c500b99c7e3ecb444b/tests/test_atomic_input_carrier_custody_run763.py), commit `eefb507513d4ab5e897340c500b99c7e3ecb444b`; **16 cases**.
- `review_atomic_input_carriers` is independent, exact-class and import-original-descriptor validation for synthetic `AtomicIntentClaim` and `AtomicPreactionWitness`. Checks text grammar, count bound, field identity across the review, reflected changes and descriptor substitution before field access.
- It performs **no I/O** and returns only a Python tuple of untrusted local values. **It is intentionally NOT wired into the existing ledger ingress** while lower-layer verification is in flight. Therefore it is *not* a claim that every underlying ledger entrypoint is now protected against in-process callback substitution.
- This does not authenticate a principal, clock, human review, source code, process integrity or independent retained witness.

### CI evidence discipline

- Run762 [#42803612314](https://github.com/Iam-2squared/ark-ai/actions/runs/42803612314) = **6/6 completed GREEN**, exact `46eaf65b45677cb7f4831dd334eaff2ba0de62a9`.
- Run763 A source [#42805745131](https://github.com/Iam-2squared/ark-ai/actions/runs/42805745131) = **in progress** at initial audit.
- Run763 A tests [#42805859637](https://github.com/Iam-2squared/ark-ai/actions/runs/42805859637) = **in progress**; Ubuntu 3/3 GREEN, some Windows jobs still running at latest check.
- Run763 B source [#42806857466](https://github.com/Iam-2squared/ark-ai/actions/runs/42806857466) = **in progress** at initial audit.
- Run763 B tests [#42806923585](https://github.com/Iam-2squared/ark-ai/actions/runs/42806923585) = **in progress**; Ubuntu 3.11 GREEN at latest check, remaining platforms pending.
- The newest exact-head **6/6 GREEN is NOT VERIFIED** until each matching job concludes success. The status commit after this document has its own exact SHA and CI run; do not transfer an older PASS or manually rerun an equivalent workflow.

## Frozen/free-only boundaries and unresolved risks

Main, Draft PR #5 (gated V3), paused Draft PR #9 (UI), frozen V1/V2/Local UI/Launcher evidence and V2 final evaluation gates are unchanged. Neither source module invokes real tools, paid compute, external APIs, sensors, camera/microphone or notification. No Candidate, new credential, physical-PC step, forced history rewrite, protected evaluation, irreversible deletion or main merge.

The new single-SQLite local pre-action intent+audit transaction (Run762) is **not** a transaction encompassing Planner, Memory, reservation, privacy, proactive or other databases. Local digests/retained state remain caller supplied and non-authenticating. Lost COMMIT receipts yield **UNKNOWN/manual review**, never an authorized automatic replay. No valid local row proves an external effect or user consent.

## Next plan / 今後の方針

1. Obtain exact-head CI conclusions for the new modules, including all Windows/Python versions; diagnose actual failures from job logs and make the narrowest semantics-preserving corrections.
2. After lower-level GREEN, design a **single-read-transaction exact claim-row comparison** for occurrence + bound-action + request digests, retaining quarantine on mismatch; do not upgrade a membership observation into proven binding or permission.
3. Review caller-retained high-water, CAS/ABA, COMMIT-UNKNOWN and process-restart semantics; integrate the detached input preflight only after verified tests and an explicit decision about the safe SQLite-ingress boundary.
4. Independently advance Planner terminal/READ recovery, Memory row/event snapshots, Personal Context privacy, proactive/observation backends, and V3 free-only identity/approval guards. All real WRITE dispatch and automatic retry remain forbidden.
