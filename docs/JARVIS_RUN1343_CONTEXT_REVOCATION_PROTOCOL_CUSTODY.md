# ARK Run1343 — Personal Context revocation protocol custody

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact work-basis HEAD: `4ee3f7e7f82f5348810c303c3e1e1a3c27cbde26`.
- Child branch: `research/run1343-personal-context-revocation-validator-custody-20261125`.

## Finding and correction

The local revocation fence pinned the MemoryScope descriptors and the hashlib/JSON primitives, but its scope-digest function and SQLite schema validator were not part of the same import-original identity check. Replacing the digest helper could make a revoked scope appear unrevoked; replacing the validator could let a tampered local ledger reach row lookup without the expected schema/integrity checks.

The revocation protocol now pins both helpers and checks their identities before constructor SQLite access and before revoke/read operations. No Memory schema or frozen contract is changed.

## Regression coverage

- Substitute the scope-digest helper and require revoke/read to deny before the private SQLite connection is opened.
- Substitute the schema validator and require constructor/revoke/read to deny before opening SQLite.
- Verify no revocation row is written by rejected synthetic operations.

## Evidence boundary

Synthetic local SQLite and fixture MemoryScope only. This is not authenticated consent, trusted storage, erasure proof, cross-store atomicity, or downstream-use authorization. No live personal data, paid/external service or compute, Candidate, protected V2 evaluation, credentials, hardware, destructive action, frozen-contract change, UI work or main merge. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no PASS is claimed.
