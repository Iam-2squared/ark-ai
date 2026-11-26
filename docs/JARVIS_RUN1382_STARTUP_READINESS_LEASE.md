# Run1382 — disconnected startup readiness lease boundary regressions

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `11d72bef1b69df06ed0c0102d6154fc4d44a0214`.
- Child PR: Draft #561, branch `research/run1382-startup-readiness-lease-rebase-20261125`.
- Child test commit before this evidence document: `dc9c1fd6e9ae4941c866eeda666ccb5acce61db4`.
- Verified unchanged source blobs on the parent: `startup_readiness_review.py` `bcbe936127ed8ef526862b2be73ecd75aac45dea`; `startup_readiness_lease_review.py` `facddb02cb5c0a53517ca8f4a00a7138a2fab7a2`.
- Rebased the disconnected Run1282 lease regression suite; prior CI does not transfer to this exact child head.

## Coverage

- Exact freshness boundary, one-millisecond expiry and acceptance below the maximum age.
- Clock rollback, negative/out-of-range values and bool-as-int rejection.
- Exact requirement tuple/carrier admission, duplicate/missing dependencies and schema mismatch.
- Blocked dependencies cannot be hidden by a READY descendant.
- Reflected snapshot mutation and replacement of requirement/result authority descriptors are denied before callback execution or lease return.

## Scope and evidence boundary

This is a synthetic, disconnected readiness diagnostic. A passing lease means only that the supplied local snapshot matches the requested component/schema identities at the supplied synthetic time. It does not establish trusted time, authenticated source identity, human consent, startup authorization, dispatch, notification, hardware readiness, or external-effect safety.

No production source, schema, public API or frozen contract is changed. No real service, credential, model, GPU, paid compute, notification, device capture, Candidate, protected V2 evaluation, destructive action, UI or main branch is touched. Exact-head CI is required; no test PASS is claimed. ARK/JARVIS remains NOT_PASSED.
