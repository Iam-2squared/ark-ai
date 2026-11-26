# Run1397 — disconnected startup readiness lease boundary regressions on current foundation

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `5628f791177668b3c74b6906208b7b92f504ad59`; parent exact-head CI run `45590765382` was GREEN (6/6) before this child was created.
- Rebased from Draft PR #561 / Run1382, whose original child HEAD `59118e37f64f0d40ac5e7a3d6294d11c2384e515` had CI run `45576193976` GREEN (6/6). That prior result does not transfer to this rebased head.
- Current `src/ark/startup_readiness_review.py` blob: `e756dfdfc26fc65d5a48c5c3e2ca11e4b081387a`; it includes the later Run1387 constructor-custody hardening.
- Unchanged `src/ark/startup_readiness_lease_review.py` blob: `facddb02cb5c0a53517ca8f4a00a7138a2fab7a2`.
- Child branch: `research/run1397-startup-readiness-lease-rebase-20261125`.

## Coverage

- Exact freshness boundary, one-millisecond expiry and acceptance below the maximum age.
- Clock rollback, negative/out-of-range values and bool-as-int rejection.
- Exact requirement tuple/carrier admission, duplicate/missing dependencies and schema mismatch.
- Blocked dependencies cannot be hidden by a READY descendant.
- Reflected snapshot mutation and replacement of requirement/result authority descriptors are denied before callback execution or lease return.

## Scope and evidence boundary

Synthetic, disconnected readiness diagnostics only. A passing lease means only that the supplied local snapshot matches requested component/schema identities at supplied synthetic time. It does not establish trusted time, authenticated source identity, human consent, startup authorization, dispatch, notification, hardware readiness or external-effect safety.

No production source, schema, public API or frozen contract is changed. No real service, credential, model, GPU, paid compute, notification, device capture, Candidate, protected V2 evaluation, destructive action, UI or main branch is touched. Fresh exact-head CI is required; no PASS is claimed. ARK/JARVIS remains NOT_PASSED.
