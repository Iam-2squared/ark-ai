# Run1389 — Proactive State Validator Vector Custody

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `9fa835e819cd9e212c2e0a2304d3c37b56293b07`.
- Child branch: `research/run1389-proactive-state-vector-custody-20261125`.

## Finding

The proactive-state protocol checks compared working field/method vectors with module-level `_ORIGINAL_*_VECTORS` aliases. The policy and state descriptor verifiers also iterated working/original tuples through strict `zip`. Replacing both sides with empty tuples made those comparisons vacuous; the purported original tuple bindings were not retained independently by the verifier.

## Correction

The protocol verifier now retains the import-time policy/state vectors, descriptor vectors and carrier types in keyword-only defaults. It rejects replacement of either the aggregate tuple aliases or their component vectors before delegating to the existing protocol checks. The policy and state class verifiers independently retain their own vectors and compare descriptors against the captured references.

The ledger class verifier already retained its own guard-vector tuple in function defaults; that path is unchanged.

## Regression coverage

- Jointly replace the policy working/original vectors with empty tuples and install a hostile `owner` descriptor; policy identity must reject before descriptor access.
- Jointly replace the state working/original vectors with empty tuples and install a hostile `scope_digest` descriptor; state construction must reject before descriptor access.
- The shared protocol guard must reject the same policy-vector replacement on a non-policy hashing path.

## Scope and evidence limits

Synthetic in-process mutation probes only. Proactive state v1 DDL/schema, row digest, policy semantics, CAS revision behavior, cooldown/window logic, public API, and denial-only authority flags are unchanged. No notification, scheduling timer, external dispatch, live personal data, credential, hardware, network action, paid/external compute, Candidate generation/promotion, protected V2 evaluation, frozen-contract change, main merge, or UI/frontend work occurred.

This does not establish process isolation, authenticated owner identity, trusted time, consent, notification permission, power-loss durability, or exactly-once external effects. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no PASS is claimed until it completes.
