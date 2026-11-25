# ARK Run1338 — Startup snapshot method custody

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact work-basis HEAD: `4ee3f7e7f82f5348810c303c3e1e1a3c27cbde26`.
- Source: `src/ark/startup_readiness_review.py`.
- Consumer: `src/ark/startup_readiness_lease_review.py`.
- Combined child branch: `research/run1342-startup-method-guard-combined-20261125`.

## Finding and correction

The startup constructor guard pinned dataclass constructors, slots and field descriptors, but did not pin the `StartupSnapshot` methods `_assert_integrity`, `state`, or `root_blockers`. The lease reviewer calls `snapshot._assert_integrity()` before accepting a diagnostic READY lease. A substituted no-op method could therefore bypass digest and dependency re-derivation for a forged snapshot.

The guard now captures and verifies the import-original method identities before consuming probe iterators or reading lease snapshot fields. Regression tests replace each method and verify early denial; a separate forged-digest lease case verifies the substituted integrity callback is never entered.

## Evidence boundary

Synthetic readiness graph and lease only. The result remains diagnostic and never grants startup, dispatch, notification, consent, trusted-clock or hardware authority. No real probes, backends, credentials, live data, paid/external service, Candidate, protected V2 evaluation, destructive action, frozen contract, UI work or main merge. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no PASS is claimed before completion.
