# ARK AI Run1118 — Personal Context revocation witness root custody

**Exact work basis:** Draft PR #8 branch `research/jarvis-foundations`, commit `a5e961876eb24adba97573bb34228740c1344d9e`.  
**Child branch:** `research/run1118-context-revocation-witness-root-rebase`.  
**Reapplied from:** older PR #248 / Run1098 revocation witness root-custody package. The previous PR #233 exact-head CI run `44982306873` was GREEN on its older base; that result does not transfer.

## Finding and change

The revocation continuity review compared its module-level field/hook vectors against a module-level tuple that could itself be rebound. Coordinated replacement of the vectors and their comparison root with equal-valued clones could therefore establish a new in-process comparison baseline.

The guard now captures the import-original `_WITNESS_VECTOR_EPOCH` object in the function's default argument and requires the live module-level root to remain that exact object before any ledger path or private SQLite access. Existing field, hook, validator, digest, retained-witness and source-path checks remain in place.

## Regression coverage

Four synthetic cases cover:
- an empty replacement root;
- an equal-valued cloned root;
- coordinated equal-valued clones of all four vector roots; and
- retention of the original root object in the validator's default argument.

The mutation cases use an uninitialized ledger carrier to prove the guard rejects before attempting to read `ledger.path`.

## Evidence boundary

This is an in-process definition-integrity guard only. A local hash prefix is not authenticated consent, independent storage, trusted time, secure erasure, proof of revocation from external copies, or permission to disclose personal data. No Memory v1 schema/API, Personal Context persistence schema or frozen contract changes. No live private data or external connector is used.

## Validation

The source patch and four synthetic regression cases are saved. **Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no PASS is claimed.** The older PR #233 CI result does not transfer.

PR #8 remains Draft/unmerged; PR #5 remains gated Draft/unmerged; PR #9 remains untouched and UI remains paused. No paid/external compute, Candidate generation/promotion, protected V2 evaluation, credentials, hardware action, destructive operation or main merge is included. **ARK/JARVIS remains NOT_PASSED.**
