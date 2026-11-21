# Run561 — Privacy erasure and durable veto receipt custody

**Draft PR #8; disconnected/synthetic only.** These local reviews do not
inspect actual personal memory, attest consent, prove forensic erasure, grant
data export, or invoke tools. All timestamps and witnesses are untrusted.

## Work basis and source/test evidence

Invocation work basis: `6a3fbe355ab683343f033c0f5665163241390a53`
(6/6 GREEN at GitHub Actions [41486457690](https://github.com/Iam-2squared/ark-ai/actions/runs/41486457690)).

1. **Erasure-assessment import-original denial checks.** Source
   `0a476051d24c4c1e0eaec6fad811d69d0e362f26`;
   test `59130e054b3114496f5190655a38fcdb3aa50e95`.
   Four denial properties are anchored at module import and compared before
   synthetic observation hashing and on every observation epoch. A patched
   always-False descriptor is an untrusted callback, not a privacy grant.
   Six new parameter-expanded synthetic cases cover the four substitutions,
   a substitution during hashing and unchanged deny-only output.

2. **Privacy veto post-COMMIT receipt verification.** Source
   `e7958a7b333955e524eeac787ac92a3386a7fa9a`;
   test `501167cd937cd2d9bd540af0fb93dea709a49041`.
   The disconnected one-way SQLite veto ledger pins original receipt and
   witness denial descriptors **before** a transaction, then verifies source,
   retained witness, appended witness and returned receipt fields after
   COMMIT and after each denial getter. Seven new synthetic cases cover
   three imported false-only substitution cases, forged receipt/witness,
   source-path retargeting after COMMIT, and normal deny-only behavior.

## Critical ambiguity and barriers

**An error after SQLite COMMIT does not undo the already persisted veto.**
Never automatically retry this write based only on a thrown exception; inspect
the local durable witness and obtain an independently retained pre-write
witness for manual reconciliation. The test exercises this distinction. This
does **not** make a cross-store exactly-once transaction or prove that a
particular caller performed a historical action.

All hashes are local consistency evidence, not trusted source identity,
authenticated revocation, consent, retention permission or forensic erasure.
No real tool dispatch, live notification, physical PC, paid/external compute,
Candidate generation, protected V2 evaluation, approval, main merge or
destructive operation occurred. Existing frozen contracts remain untouched.

## Validation boundary

New-case counts above are authored test cases, **not independently executed
local pytest PASS counts**. CI conclusions are scoped to their exact HEAD.
An in-progress or failed earlier-head run must not be promoted to GREEN.
