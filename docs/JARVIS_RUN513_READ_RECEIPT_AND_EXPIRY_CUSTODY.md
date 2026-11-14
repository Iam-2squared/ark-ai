# Run513 — retained registered READ diagnostics and Memory expiry custody

**Status:** two independent local-first source/test hardening packages on Draft PR #8, no backend execution, real consent, trusted clock, data disclosure, deletion or WRITE. Overall JARVIS **NOT_PASSED**.

## Exact work bases and normal GitHub writes

Initial work-basis branch HEAD: 4b351fbbd7ea2a5c514f6973cc2cbcc90ec9cfa1.

### Package A — registry-bound disconnected READ receipt recheck

- Source commit de14e77d7030fd3f1206d816d2ecfbde7478406b.
- Source path src/ark/agency/disconnected_registered_read_recheck.py, blob d23536f9b2bc37b61e34c99508ffd142929c7a39.
- Tests commit 04212aecd43ed36b8b0952e29e4391791866332f.
- Test path tests/test_disconnected_registered_read_recheck_run513.py, blob 8d267304e8a1fa5d2990cb84e1a19bb7cdb47c98.
- **21 authored pytest cases** including parameter expansions.

The prior READ-only preflight is a diagnostic, not a durable grant. The new opt-in verify function accepts an **exact original receipt**, immutable ToolRegistry, PermissionGate, ToolCall, bounded exact tuple of CapabilityGrants and caller-supplied synthetic time. It pins the original receipt, ToolCall stored-carrier fields, grant fields and registry revision, reruns the zero-dispatch registration/policy check, rejects stale scope/time/binding or forged result, and checks identity and non-authority flags after callbacks. The computed ToolCall request ID is compared by **value** because its getter rehashes a fresh string; stored original fields are compared by identity. Returns None, never an execution token.

Threat model: reflected dataclass value-equal carrier replacements, stale receipt after grant expiry, registry READ-vs-WRITE mismatch, forged recheck callback. It does **not** authenticate a caller's claimed clock, grants, registry origin or receipt custody, and does not invoke a ToolBackend, access files, or grant external READ/WRITE.

### Package B — Memory expiry preview retained report epoch

- Source commit a63fb36e8d669345ce9310002260d1099b4fea82.
- Source path src/ark/memory/expiry_candidate_preview.py, blob b93bd66c6c9ae8e70013187750fd02f99d9a6584.
- Tests commit da76f98ae993cc0c5e114537a0c193a50f1bd4b3, **final Run513 PR #8 source/test HEAD**.
- Test path tests/test_memory_expiry_retained_carrier_run513.py, blob 8e68c73df8621e4e82cf0113d3c2089f05802966.
- **10 authored pytest cases** including parameter expansions.

The existing read-only expiry verification re-derives the page from local SQLite. It now additionally pins the initial receipt field carriers, refuses equal-valued replacements during the second read, checks both original and latest receipt authority flags after the final local scan, and performs another fail-closed receipt/source check after the getter callbacks. Synthetic expiry preview never calls purge_expired, returns private content, claims physical erasure, or provides consent.

Threat model: a benign/reflective reentrant callback mutating frozen receipt fields, a late authority flag that was false on the first check, and a forged latest page receipt. This reduces TOCTOU drift but is not an atomic cross-transaction evidence claim or independently authenticated owner/custody proof.

## Verification and boundaries

- **31 authored pytest cases** (21 agency + 10 Memory), not a claim of 31 independently executed local passes.
- GitHub Actions initial exact final source/test HEAD da76f98ae993cc0c5e114537a0c193a50f1bd4b3: [CI 41245181320](https://github.com/Iam-2squared/ark-ai/actions/runs/41245181320), **IN PROGRESS at documentation preparation**. Do not infer six-environment GREEN from previous commits.
- Independent local pytest and Ruff **not run** because the working container cannot resolve the public GitHub repository for checkout. Only normal Github Contents API files/commits; no raw Git object/ref bypass.
- Frozen Memory contracts at src/ark/memory/contracts.py (blob b6e93821ecd69270a7634aceb20775dc36e9953c) and Agency contracts at src/ark/agency/contracts.py (blob 13f1bb725f9c2c783e29402ca4a6e0f86b850ef9) remain unchanged.
- No paid/external GPU/API, real training/Candidate, physical PC, protected V2 final evaluation, main merge, real ToolBackend dispatch or unknown WRITE replay.

## Next plan

Check exact-head CI and fix source/test only if a genuine failure occurs; then continue durable CAS/event snapshot corroboration, Planner UNKNOWN WRITE manual-only evidence, registry-bound mock READ fixture integration after exact-head GREEN, trusted-clock audit-before-action contracts, scheduler restart duplicate prevention and scoped privacy revocation with no actual side effect.


### Package C — proactive scheduler freshness report no-authority fence

- Source commit 53bc3853ece87de03fa7473617af4935de31032c.
- Source path src/ark/proactive_synthetic_freshness_review.py, blob c1740cca06e2c8055f9ba87e077aa4ac0bcad5eb.
- Test commit / updated final PR #8 source+test HEAD af2cca7f6cbdd2f2719a9ac238082f203f9776e3.
- Test path tests/test_proactive_freshness_authority_run513.py, blob 3e702ed5729b6edcf299e77ed5b354d780658fd9.
- **10 authored pytest cases** (three authority flags each tested against True and numeric zero, three reflected-denial mutation targets, one no-effect control).

A synthetic prepared scheduler marker still cannot grant real notification, Tool dispatch, or automatic replay. The result-construction validation now rejects any authority flag that is not the exact False object, then rechecks the source epoch, constructed trigger-history witness, and returned result field identities after all those getter callbacks. A local freshness receipt remains a diagnostic under caller-supplied time and policy: no notification or real-world scheduling occurs.

**Revised Run513 PR #8 authored total: 41 cases** (21 READ receipt + 10 expiry + 10 scheduler). The earlier 31 count is the package A+B intermediate total only. Previous CI run 41245181320 validates only the A+B intermediate source HEAD; it does not validate this C package. Exact latest source/test CI is [run 41245451032](https://github.com/Iam-2squared/ark-ai/actions/runs/41245451032), **QUEUED at package preparation**, so there is no latest-head 6/6 GREEN claim here.
