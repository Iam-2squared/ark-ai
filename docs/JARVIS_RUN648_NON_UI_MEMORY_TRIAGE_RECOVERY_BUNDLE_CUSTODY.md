# ARK AI — Run648 non-UI manual-COMMIT and detached-recovery custody

**Scope:** JARVIS-core, isolated/reversible non-UI hardening on Draft PR #8. No protected evaluation opening, main merge, UI/frontend development, real tool dispatch, credential, GPU, paid API or Candidate work. JARVIS remains **NOT_PASSED**.

## Work basis and packages

- Initial live PR #8 work-basis HEAD: `b825848760608e062b3f09142ad2cc6688aae0f2`. This was newer than the canonical Run646 checkpoint and carried Run647's separate package A/B/C. Run646 [#42140329053](https://github.com/Iam-2squared/ark-ai/actions/runs/42140329053) was **6/6 GREEN**; Run647's HEAD [#42148123675](https://github.com/Iam-2squared/ark-ai/actions/runs/42148123675) was **3 Ubuntu GREEN, Windows IN PROGRESS** at initial read, subsequently observed **6/6 GREEN**.
- Package A, `src/ark/memory/postcommit_uncertainty_review.py`, saved commit `647269fac7df1857e5e7cb21efa7528061196b69`: checks the original `MemoryCommitTriage` result type, constructor, seven field descriptors, three lookup hooks and four denial properties before inspecting retained private SQLite; rechecks across snapshot, digest, constructor and denial callbacks. The prior retained-token and row-image guards remain intact. Only manual classifications, no writer attribution or automatic retry.
- Package A test file `tests/test_memory_triage_report_carrier_preaccess_run648.py`, commit `44bbeebf55fbc51f4d7cac3c3c1a0b67ee97dcc8`: **12 authored cases**, including preinstalled poisoned report fields/hooks, reentrant swaps after a snapshot and just before the report constructor, and normal manual-only unchanged receipt. This is case count, NOT test PASS evidence.
- Package B, `src/ark/agency/synthetic_plan_recovery_bundle_review.py`, commit `7566d349ac80e7f5803f709824149655bb7bafed`: captures import-time immutable references for the detached plan-recovery bundle's two slots, constructor/lookup hooks, and three deny-only properties; checks before decoding retained bytes, before emitting the bundle after serialization and after callback boundaries. Explicit rechecks of authority denials are made before returning captured bundle. This is offline forensic serialization, not a secure signature or independent custody guarantee.
- Package B tests `tests/test_recovery_bundle_carrier_preaccess_run648.py`, commit `777627cac06917f073f3fce05ee82b33299f0745`: **11 authored cases** for poisoned slots/hooks/denials/constructor, digest reentrancy and normal two-step offline restoration. No real backend is invoked.

## Validation limitations and safety

- At initial evidence write: latest source-plus-test HEAD `777627cac06917f073f3fce05ee82b33299f0745` had [Actions #42149518260](https://github.com/Iam-2squared/ark-ai/actions/runs/42149518260) **QUEUED**, **NOT six-job GREEN**.
- Each new test count is an authored parameterized case count, not a PASS count. No local pytest/Ruff or unavailable physical-PC test is claimed; GitHub Actions must determine Python 3.11/3.12/3.13 and Windows/Ubuntu parity.
- Potentially failed tests must be repaired from actual CI logs using only normal safeguarded GitHub Contents write, with no force push, raw object bypass, or safety weakening.
- Python class/slot identity is an in-process defense against fixture-driven mutation, not security against unrestricted hostile interpreter access. Hashes do not authenticate an independent witness, external WRITE outcome, consent, clock, real-world exactly-once effects or user identity.
- All frozen V1/V2/Local UI/Launcher contracts and evaluation evidence remain untouched; PR #5 and PR #9 remain Draft/unmerged, UI paused.

## Next plan / 今後の方針

1. Confirm the exact-head 6-job CI, repair any real lint/pytest failure without changing authority semantics, then obtain new exact-head evidence.
2. Extend Memory CAS uncertainty model with two-handle row/event consistency and expiry-bound recovery without replay.
3. Continue Planner persistent UNKNOWN/terminal propagation and independently audited mock WRITE reservation/occurrence before considering integrations.
4. Keep disconnected scheduling/observation, privacy-safe Personal Context and zero-cost V3 guard work reversible and isolated; no paid or protected gate without explicit authorization.
