# Run1371 — Personal Context continuity guard self-custody

## Exact basis

- Parent: Draft PR #544, branch `research/run1365-personal-context-revocation-custody-rebase-20261125`.
- Exact parent HEAD: `191821bf6377e02d03632c92dfc91f1dc46c4b9b`.
- Child branch: `research/run1371-context-continuity-guard-self-custody-20261125`.
- Source: `src/ark/personal_context_revocation_continuity_review.py`.
- Regression: `tests/test_context_revocation_continuity_guard_self_custody_run1371.py`.

## Finding and correction

The retained revocation-continuity reader checked its hash, JSON, witness-carrier and schema-validator dependencies, but internal entry/recheck calls resolved `_require_original_witness_carrier` through its mutable module binding. A replacement no-op could bypass those identity checks before the private SQLite snapshot.

The module now retains `_ORIGINAL_WITNESS_GUARD`, checks that the mutable binding still names that exact function, and routes internal calls through the retained alias. A substituted guard is rejected before the ledger connection callback.

## Regression coverage

The synthetic regression replaces the mutable guard with a callback and requires the retained original guard to reject the replacement before either callback execution or private SQLite access.

## Scope and evidence limits

The revocation continuity schema, witness format, MemoryScope contract, public APIs, retention and denial-only semantics are unchanged. This does not establish authenticated consent, trusted time, independent storage custody, physical erasure, cross-store atomicity, an atomic downstream-use lease, or disclosure/dispatch authority.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed. Synthetic local SQLite only; no live personal data, paid/external compute, Candidate, protected V2 evaluation, credentials, hardware, destructive action, frozen-contract change, main merge, or UI/frontend work occurred. PR #5/#8/#9 and parent PR #544 remain Draft/unmerged; ARK/JARVIS remains NOT_PASSED.
