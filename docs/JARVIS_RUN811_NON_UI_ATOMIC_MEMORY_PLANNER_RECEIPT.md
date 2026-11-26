# ARK AI — Run811: registry-bound atomic intent, expiry geometry, detached Planner digest (NON-UI / FREE-ONLY)

Saved-at preparation observation (Asia/Tokyo/JST): 2026-11-12T15:24:11+09:00. This ordinary wall-clock statement is NOT trusted ARK time or a proof of consent.

## Work basis and immutability

- The initial independently fetched PR #8 HEAD was `d8385d710a28f228824ca375cd1719947691ec65`; prior `docs/PROJECT_STATUS.md` blob was `80392fadaad1a5be7aea4a22dbb45c5b1feb2ab2` (Run810).
- Target: `research/jarvis-foundations` / [PR #8](https://github.com/Iam-2squared/ark-ai/pull/8), OPEN/DRAFT/UNMERGED.
- Protected [PR #5](https://github.com/Iam-2squared/ark-ai/pull/5) remains Draft/unmerged at `805b377697472268db02650a89c7a94b1c5337c8`; paused UI [PR #9](https://github.com/Iam-2squared/ark-ai/pull/9) remains Draft/unmerged, untouched at `3b49048dd70eebcb6268299b9ecef4e301bbc0fd`.
- No frozen V1/V2/Local UI/Launcher contract, evaluation or evidence changed. No paid service, external GPU, real Candidate generation, protected evaluation, new identity/credential, backend dispatch, physical PC operation, deletion or merge.

## Package A — registry-bound inert atomic intent stability

- Source `src/ark/agency/disconnected_atomic_registry_bridge.py` updated at `0eeb6d7c3e487839532b4102d61ff9f611ed4890`. Original ToolCall source descriptor and synthetic intent carrier/constructor are checked, and a per-instance shadow of `ToolRegistry.bind` is refused. Call identity remains pinned before and after reentrant registry bindings and before digest/claim construction. Existing digest and exact WRITE checks preserved.
- Tests `tests/test_atomic_registry_intent_stable_inputs_run811.py` added at `bef6dd207e7ffa66ff6ac4f758e71f95b1646f96`, **8 new cases** including altered instance method, constructor, slot and request-ID descriptor plus positive inert behavior.
- No real ToolBackend, approval issuer or exactly-once effect proof. Current test-head CI [#43166926914](https://github.com/Iam-2squared/ark-ai/actions/runs/43166926914) **IN PROGRESS** at first inspection, not a verified GREEN.

## Package B — Memory expiry page/truncation geometry

- Source `src/ark/memory/expiry_cohort_review.py` updated at `7a8333640bb2c9f3aa68f786f440294f2be81cae`. A local receipt cannot claim `has_more=True` for zero selected candidates; a retained multi-scope cohort cannot claim more truncated scopes than aggregate visible candidates. These reject internally impossible local pagination without reading contents or enabling `purge_expired`.
- Tests `tests/test_memory_expiry_truncation_geometry_run811.py` added at `786423d377493e5a7ecbdef8cc773cc03e7ccb7b`, **9 new cases**, including legitimate empty untruncated pages, legitimate nonempty overflow, malformed pages and forged retained cohort.
- Source test-head CI [#43167108541](https://github.com/Iam-2squared/ark-ai/actions/runs/43167108541) **IN PROGRESS / QUEUED** during inspection; not GREEN-verified. Caller clock, independent scope inventory and cross-scope atomicity are still NOT authenticated.

## Package C — detached Planner quarantine digest proof of *local self-consistency*

- New `src/ark/agency/disconnected_dependency_digest_review.py` at `1d93937c2fb371e618e2180ae0605b943afe87e2`; test `tests/test_detached_dependency_digest_run811.py` at `b256bf208f35a9218011064b6b25e0b5c747b225`, **16 new cases**.
- This read-only module reserializes a caller-supplied bounded, sorted `DisconnectedDependencyClaim` DAG and its corresponding `DisconnectedDependencyProjection` HOLD labels. It recomputes the exact local quarantine SHA over canonical source-domain bytes and checks the pinned source identity/protocol and False-only authority properties. Cases exercise changed digest, matrix, reasons, topology, effects, swapped membership, malformed carrier and code/descriptor substitution.
- This only verifies that a local receipt is consistent with provided local claims. It does **NOT** independently re-evaluate the multi-store WRITE matrix, certify completeness of the claimed plan, prove external provenance, remove HOLD, authorize READ/WRITE, permit retry or invoke tools. No code in the existing in-flight Run810 restart-join path was edited. Test-head CI [#43167507976](https://github.com/Iam-2squared/ark-ai/actions/runs/43167507976) was **QUEUED** at first inspection.

## CI and prior failure evidence

- Earlier Run809 checkpoint `2fc5375c8d216fd5d4d3cfa873851aa5129cd5ce` [#43157691647](https://github.com/Iam-2squared/ark-ai/actions/runs/43157691647) was **GREEN 6/6**, independently confirmed.
- Run810 source/test head `c97cbbb7f882a574626120084f9817ab2a2d14c7` [#43164712185](https://github.com/Iam-2squared/ark-ai/actions/runs/43164712185) was **GREEN 6/6**.
- Run810 report-only head `3fc3e51e6ac0b01dfa3027bd6c6f85e1062426ab` [#43165560549](https://github.com/Iam-2squared/ark-ai/actions/runs/43165560549) was **FAIL 5/6**: Ubuntu Python 3.12 job `131006498501` reported `1 failed / 13,981 passed / 1 skipped` in an existing cross-process revocation race `tests/test_privacy_revocation_cross_process_run425.py[1]`. One process emitted `REVOKED`; the second ended with a child `AssertionError` because its rejection text did not meet the test's `already revoked` expectation. The captured parent log does **not** disclose the original rejection text, so the underlying failure is NOT proven. We did not weaken the test or guess a production fix. Inspect a new exact-head occurrence and capture the actual child diagnostic if repeated.
- Run810 final checkpoint head `d8385d710a28f228824ca375cd1719947691ec65` [#43165898946](https://github.com/Iam-2squared/ark-ai/actions/runs/43165898946) had **Ubuntu 3/3 GREEN and Windows 3 IN PROGRESS** at last inspected snapshot.
- New code has not been locally fully checked out or run with `ruff`/`pytest`; automated PR CI on exact commit HEAD is authoritative. No duplicate equivalent CI workflow has been launched.
- The eventual latest status commit creates another HEAD not present at report preparation. Its six-job result must be checked independently.

## Next plan / 今後の方針

1. Verify all six jobs of the exact final checkpoint HEAD and the three feature/test heads, read individual failure logs before any semantics-preserving repair. Do not borrow older GREEN results.
2. Once lower-layer exact-head GREEN is established, bind detached Planner digest checks to disconnected journal startup/WRITE quarantine, with independent store inventory validation; never auto-replay ambiguous actions.
3. Strengthen durable Memory COMMIT-UNKNOWN/revision CAS and coherent expiry review; investigate real revocation cross-process startup failure rather than weakening privacy tests.
4. Expand immutable Registry/PermissionGate and audit-before-action only in disconnected mock lanes; inspect Personal Context retention, proactive occurrence fences, Observation fixture adapters and free V3 identity guards.
5. Maintain frozen contracts, PR #5/#9 gates and UI pause. **ARK/JARVIS remains NOT_PASSED.**

## Verified CI compatibility correction after the three packages

The first atomic registry test-bearing [#43166926914](https://github.com/Iam-2squared/ark-ai/actions/runs/43166926914) failed in Ubuntu 3.11, 3.12 and 3.13 at the existing `tests/test_atomic_bridge_dependency_epoch_run783.py::test_bind_callback_cannot_swap_sha_before_request_digest`. Its safety refusal was correct but emitted `invalid registry-bound intent source`, outside the frozen test's accepted `registered intent binding refused` or `registry intent digest or grammar changed` error taxonomy. No backend ran and no forged hash executed. Source-only correction at `253f4c0105ba8a5310e6800c40d14bc65051a5d5` preserves the early instance-bind rejection but uses the original `registered intent binding refused` diagnostic; **no test assertion was relaxed**. A newer exact-head CI is required before declaring GREEN. That source fix follows the initial report and its original test-submission claims; do not claim earlier runs validate it.
