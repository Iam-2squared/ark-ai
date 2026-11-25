# Run1370 — Personal Context revocation guard self-custody

## Exact basis

- Parent: Draft PR #544, branch `research/run1365-personal-context-revocation-custody-rebase-20261125`.
- Exact parent child HEAD at fork: `191821bf6377e02d03632c92dfc91f1dc46c4b9b`.
- New child branch: `research/run1370-personal-context-guard-self-custody-20261125`.
- Source: `src/ark/personal_context_revocation_review.py`.
- Regression: `tests/test_context_revocation_guard_self_custody_run1370.py`.

## Finding and correction

Run1365 pins the import-original scope-digest helper and SQLite schema validator, but the guard function that checks those identities was still called through its mutable module binding. Replacing `_require_original_scope_digest` with a no-op could therefore bypass the helper checks at constructor, digest, revoke, and read boundaries.

The source now retains `_ORIGINAL_SCOPE_DIGEST_GUARD`, verifies that the public guard binding still refers to that exact function, and routes all internal guard calls through the retained alias. A substituted guard is rejected before SQLite access or scope hashing.

## Regression coverage

Synthetic tests replace the mutable guard binding with a no-op and require rejection before:
- reopening an existing ledger in the constructor;
- scope digest processing;
- revocation writes;
- revocation reads.

The tests assert that no replacement connection callback runs and that the existing synthetic ledger remains empty.

## Scope and evidence limits

MemoryScope v1, revocation v1 DDL, public APIs, retention, and denial-only semantics are unchanged. This does not establish authenticated consent, trusted time, independent storage custody, physical erasure, cross-store atomicity, an atomic downstream-use lease, or disclosure/dispatch authority.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed. Synthetic local SQLite only; no live personal data, paid/external compute, Candidate, protected V2 evaluation, credentials, hardware, destructive action, frozen-contract change, main merge, or UI/frontend work occurred. PR #5, #8, #9, and parent PR #544 remain Draft/unmerged; ARK/JARVIS remains NOT_PASSED.
