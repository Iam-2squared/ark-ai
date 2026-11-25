# JARVIS Run1282 — Startup readiness lease regression

## Exact basis

- Repository: `Iam-2squared/ark-ai`.
- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `ddc4a574437361059552615ceb44936a628555dc`.
- Child branch: `research/run1282-startup-readiness-lease-tests`.
- Test commit: `669d6f45dec256f18090f3058a704b4a55e20c6d`.
- Boundary-expectation correction: `edad36fec80eb596e1dfceae11a64886505eba68`.

## Regression coverage

The previously untested `review_synthetic_startup_lease` path now has focused tests for:

- exact freshness boundary acceptance and one-millisecond expiry;
- clock rollback, negative/out-of-range times, and bool-as-int rejection;
- exact tuple and exact requirement-carrier admission;
- duplicate/missing dependencies, blocked dependency propagation and schema mismatch;
- reflected snapshot mutation;
- replacement of the requirement validator and result denial descriptor before callbacks execute.

## Scope

This is a synthetic, disconnected readiness diagnostic. A passing lease means only that the supplied local snapshot matches the requested component/schema identities at the supplied synthetic time. It does not establish trusted time, authenticated source identity, human consent, startup authorization, dispatch, notification, hardware readiness, or external-effect safety.

No real service, credential, model, GPU, paid compute, notification, device capture, Candidate, protected V2 evaluation, frozen contract, UI, or main branch is touched. Exact-head CI is required; no test PASS is claimed before CI reports it.
