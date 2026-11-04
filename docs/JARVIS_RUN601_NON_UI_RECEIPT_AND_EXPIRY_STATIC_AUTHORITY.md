# Run601 — Retained READ and Memory expiry descriptor custody (non-UI)

**Work-basis:** PR #8 `research/jarvis-foundations` at `06d19a1cb92863dc48a7db4f7efdab76e3265561`. This is a source-and-fixture hardening run on a Draft/unmerged branch. It changes no frozen contracts, model, UI, launcher, real execution backend or hardware.

## Package A — retained READ-cycle verification, before getters

- Source `src/ark/agency/disconnected_read_cycle_receipt_recheck.py`, commit `a3c42d5f1a0653389432388298e79d0c84a1b670` (starting blob `4b289e3ec3a28e6af36dc588dafeaa1c6096fd60`).
- Regression `tests/test_read_cycle_retained_original_denials_run601.py`, originally saved `83b34985f52e5947c970e537cd768f50f4eb7e50`; subsequent import-layout-only corrections `6e4ed18a3828ec9d610140a750efef72b986c58d` and `5f7244c9005d855c3297e41ff7a4e23da24c31b3`. **9 authored parameter-expanded cases**, not a local pytest PASS count.
- Import-time receipt class and four original deny-only property descriptors are pinned. Both retained and independently recomputed mock receipts reject a counterfeit property returning literal `False` **without invoking the counterfeit getter**, at entry and after detached simulation. Rechecks bracket each deny-only getter and retain exact-field identity.
- Earlier unit tests already cover stale digests, wrong scope/expiry, WRITE misclassification and non-PENDING plans. No ToolBackend is accessible to this verifier, the source PlanGraph remains PENDING, and the gate's one-shot WRITE tokens are not spent.

## Package B — Memory expiry authority: no hostile class-level descriptor execution

- Source `src/ark/memory/expiry_candidate_preview.py`, commit `765c7222cfb2876f14f2afc9bc120bff3ba53c3f` (starting blob `bf733f137736b451b0be236a877c8b7f2edff042`).
- Regression `tests/test_memory_expiry_static_denials_run601.py`, commit `afbc4a564e56ef74280533fda1c497a463a98dfd`: **11 authored parameter-expanded cases**, not local pytest PASS.
- The former `getattr(report_class, flag)` could execute an adversarial descriptor's class-level `__get__`, which could itself impersonate the expected original property. New checks use `vars(original_class).get(...)` and `inspect.getattr_static(report, ...)` before any instance getter. Tests install a descriptor that returns the original property on class access and `False` on instance access; assert it is **never invoked** on either preview or retained re-verification.
- No expiration deletion, data disclosure, clock attestation, actual owner consent or future purge authorization follows from an inert expiry preview.

## CI and correctness discipline

- Run600 exact checkpoint HEAD `06d19a1cb92863dc48a7db4f7efdab76e3265561` has independently checked **six-job GREEN**: [#41789059180](https://github.com/Iam-2squared/ark-ai/actions/runs/41789059180), Ubuntu/Windows Python 3.11/3.12/3.13. This evidence predates all Run601 edits.
- First READ-test HEAD [#41794402213](https://github.com/Iam-2squared/ark-ai/actions/runs/41794402213) and Memory source HEAD [#41794577473](https://github.com/Iam-2squared/ark-ai/actions/runs/41794577473) failed the repository-wide Ruff `I001` **in the newly added READ test**, before running pytest. The Memory test HEAD [#41794630629](https://github.com/Iam-2squared/ark-ai/actions/runs/41794630629) inherited this lint failure. The source code's runtime tests were therefore **not validated by these failed runs**. Subsequent READ-test import-layout commits were made through the normal Contents API; their exact-head GREEN remains subject to checking, not presumed.
- Any new docs/checkpoint commit triggers a distinct ordinary workflow. Do not manually duplicate a CI run. Record latest run/HEAD results only after reading them; never equate test definitions with executed PASS.

## Separate free-only V3 read-only observation

- PR #5 at `805b377697472268db02650a89c7a94b1c5337c8` remains Draft and gated. Its frozen `docs/v3/CONTRACT.md` blob is `b44f7b0e7e619c225ab662ed9c1fc8deae2b1e23`, untouched.
- PR #5 `src/ark/learning/preflight.py` blob `e768983b8a924ba6c5a36e21c14338b7b83ee19d` visibly contains device, VRAM, allocated/reserved and wall-time cross-checks. `src/ark/learning/export_plan.py` blob `a5c9786731a982fec5e454d0e961e4e5fdc60e42` visibly includes resolved-path checks. An older PR #8 `V3_FREE_GUARD_REVIEW.md` described these *at an older PR #5 HEAD* and must not be treated as a live unresolved defect list without re-verifying current tests and the full implementations.
- Neither those source observations nor CI authorize real Candidate creation, paid training, protected V2 final evaluation, or promotion.

## Next integration dependencies / 今後の方針

1. Obtain six-job GREEN for the final Run601 HEAD, then isolate any regressions by actual job logs and apply only semantics-preserving fixes. Respect concurrent branch HEAD.
2. Audit the retained READ verifier's last callback/return boundary and the Memory expiry preview's read-snapshot/overflow budget without enabling backend or deletion.
3. Continue Memory generation CAS COMMIT-UNKNOWN manual readback and Planner mixed-state crash recovery in separate lanes. The synthetic occurrence+authorization+audit writes remain separate SQLite commits: they are not an atomic external exactly-once guarantee.
4. Integrate disabled-by-default ToolRegistry/PermissionGate and audit-before-*mock*-action only after exact lower-layer GREEN. Keep Personal Context, observation fixtures and proactive scheduling privacy/occurrence constraints; UI PAUSED.

**Hard boundaries:** No new paid/API/GPU resources, credentials, real device access, physical PC actions, destructive operation, protected evaluation, Candidate weights, promotion, frozen artifact modification or main merge. PR #5/#8/#9 Draft/unmerged; ARK/JARVIS/V3 **NOT_PASSED**.
