# ARK AI Run804 — protected non-UI work lanes and observation input privacy

This is **reversible, disconnected, free-only, non-UI groundwork** on Draft PR #8. No claim of JARVIS PASS, a real user permission, backend execution, hardware capture, external provenance, or a CI outcome is implied.

## Exact saved work and source basis

The last inspected existing PR #8 work-basis before our writes was `f4fe57a2815f2f9aa772954e5cd26f2abbd3cffe` (Run803 technical report). Previous Run802 checkpoint `e4ca6d7db9bbd6185d7d1125823ea37a325b3886` is historical, not the present test HEAD. Two independent work packages were saved sequentially through the normal GitHub Contents API after re-reading PR #8 HEAD immediately before every write.

1. **Explicit protected-path quarantine for the non-executing work-lane selector.** Source `src/ark/agency_synthetic_lane_selector_review.py`, commit `c8e2ba086a79e8238689a6964412a879584312df`. Optional `protected_paths` is a bounded, canonical exact tuple with the same lexical path validation used for in-flight paths. A candidate touching a protected subtree or its parent is deferred as `protected_path` before eligible selection. Prefix-sibling paths are not rejected. The previous default call retains its original decision and digest; all selector receipts still explicitly deny GitHub writes, execution and spending.
   Test `tests/test_agency_protected_lane_selection_run804.py`, commit `62c0218bcae5c25113c339b2b899e3a0d37e36a7`, **13 parameterized cases**: paused frontend/Local UI/screenshots; parent/child collision; harmless sibling; default compatibility; order/digest; six invalid inputs; no bypass from alleged CI green; no authorization for completed work. This is an **opt-in planning diagnostic**, not an enforceable repository permission or authenticated UI freeze. No frontend code or PR #9 branch changed.

2. **Fail-before-getter observation lineage reuse fence.** Source `src/ark/observation_reuse_review.py`, commit `10ffd79ce5381c3cdf67c4de906125db4b7e97c4`. Pin import-original slotted witness and observation envelope fields, lookup hooks and identity getter. Verify them before reading cached privacy/source metadata and after reentrant historical/current lineage callbacks. This prevents a swapped Python property from consuming private fixture labels before the existing value-only epoch check detects drift. Existing result-initializer mutation tests stay intentionally injectable, and no frozen contracts are altered.
   Test `tests/test_observation_reuse_input_descriptor_run804.py`, commit `179d206331dd00fad7f1fd3e67c4852898a0a70f`, **7 parameterized cases**: five early getter substitutions, late lineage callback substitution, clean non-authorizing reuse. This protects against a limited in-process fixture misconfiguration, **not** compromised Python interpreter code or external device/consent verification.

Both new test files had syntax independently checked with `python -m py_compile` in the local working environment; this is **not** full pytest or Ruff. Source was not locally run against the full repo because no authenticated local checkout exists here.

## Actual CI evidence at report preparation

- Run802 checkpoint HEAD `e4ca6d7db9bbd6185d7d1125823ea37a325b3886`, [CI #43116886052](https://github.com/Iam-2squared/ark-ai/actions/runs/43116886052): **5/6 GREEN, 1 FAIL**. Ubuntu Python 3.12 failed a pre-existing audit subprocess gate; later Run803 changed its *diagnostics*, not audit authority.
- Existing Run803 HEAD `f4fe57a2815f2f9aa772954e5cd26f2abbd3cffe`, [CI #43124776142](https://github.com/Iam-2squared/ark-ai/actions/runs/43124776142): Ubuntu 3/3 GREEN; Windows 3/3 IN PROGRESS at last inspection.
- New Run804 test-bearing HEAD `179d206331dd00fad7f1fd3e67c4852898a0a70f`, [CI #43126442391](https://github.com/Iam-2squared/ark-ai/actions/runs/43126442391): QUEUED at last inspection. **20 new cases submitted; six-job GREEN remains UNVERIFIED.** The report/checkpoint commits also produce new exact HEADs with their own CI and must not inherit older results.

## Frozen status and free-only boundaries

V1/V2/Local UI/Launcher frozen evidence, V3 Contract 1 and the protected V2 final evaluation remain unchanged. PR #5 Draft/unmerged; PR #8 Draft/unmerged; PR #9 Draft/unmerged, UI development **paused**, no branch changes. No paid/external compute, API, GPU, subscriptions, accounts, credentials, model generation, Candidate promotion, real ToolBackend, action/notification, physical-PC work, destructive change or main merge. A caller's `protected_paths` and `claimed_green` do not authenticate owner control or CI evidence. A local checksum is not an independently signed release claim.

## Dependency-aware next plan / 今後の方針

1. Check six jobs on the **checkpoint-result** HEAD. If FAIL, inspect exact job logs; smallest correction through the normal Contents API only. Never re-run duplicate workflows.
2. Inspect the enhanced Run803 multi-process audit/Memory child stderr when a failing run provides it; do not weaken SQLite alias denial based on guesses. Keep isolated modules' in-flight CI paths untouched.
3. Bind actual user-paused/frozen repository path policy into a separately reviewed workflow only after trusted policy inputs and exact-HEAD GREEN; until then selector `protected_paths` remains caller asserted and non-authoritative.
4. Continue Memory CAS/ABA and COMMIT-UNKNOWN diagnosis, Planner restart quarantine, audit-before-mock-execution and restart-safe one-shot PermissionGate, subject to lower-layer GREEN. No real WRITE replay.
5. Maintain free-only V3 identities/approvals and privacy-minimal observation fixtures. Preserve all Draft/frozen gates; ARK/JARVIS overall **NOT_PASSED**.
