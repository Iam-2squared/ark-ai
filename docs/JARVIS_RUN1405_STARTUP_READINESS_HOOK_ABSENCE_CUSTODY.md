# Run1405 — startup readiness carrier hook absence custody

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `36368ccc4160727c79fb24704a675d589575b414`.
- Child branch: `research/run1405-startup-readiness-hook-absence-custody-20261125`.
- Child HEAD before this evidence document: `eb5d0602be9fb637c66ddfa16766018068210cac`.
- Source file: `src/ark/startup_readiness_review.py`.
- Source blob after implementation: `0921b983be723d2378583919a1715731fc22e6bf`.

## Finding and correction

The startup evaluator retained the `__new__`, `__getattribute__` and `__getattr__` hook values for each of its three exact carrier types using `vars(kind).get(name)`. An absent hook therefore appeared as `None`, and an explicitly installed `None` could pass the identity comparison. This left a class-lookup-policy change outside the constructor/field descriptor epoch.

The guard now captures a unique absence sentinel in its keyword-only default arguments and stores that sentinel in the original hook vectors. It checks both class-namespace membership and descriptor identity for every hook on every carrier. Replacing the sentinel or hook-name vector is rejected before probe iteration or carrier field reads.

## Regression coverage

- Explicit `None` for each of the three hooks is rejected on `StartupComponent`, `ComponentResult` and `StartupSnapshot`.
- The exact absence sentinel installed as a hook is rejected.
- Sentinel replacement and equal-valued hook-name vector replacement are rejected.
- A hostile `__getattribute__` hook is rejected before the caller probe generator is consumed.
- The original startup carrier hook inventory remains accepted.

Synthetic disconnected readiness inputs only. No backend, permission, device, notification, hardware, dispatch or startup activation is invoked.

## Scope and evidence limits

The readiness graph schema, digest, dependency semantics, public carrier fields, readiness states and frozen contracts are unchanged. The evaluator remains a synthetic diagnostic; this does not establish trusted time, authenticated runtime identity, consent, startup authorization, device readiness, dispatch authority or automatic replay. It is local in-process class/descriptor integrity only, not a process sandbox.

No live user data, credentials, paid/external compute, Candidate generation/promotion, protected V2 evaluation, frozen-contract change, destructive operation, main write/merge or UI/frontend work occurred. PR #5/#8/#9 remain under their existing gates. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no PASS is claimed.
