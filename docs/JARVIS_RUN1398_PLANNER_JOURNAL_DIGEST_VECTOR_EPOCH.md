# Run1398 — PlannerJournal digest vector epoch custody

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `ae3c330f11513c782bed9703febc8ac0c3a31747`; parent exact-head CI run `45590765382` was GREEN (6/6) before this child was created.
- Child branch: `research/rebase-run1398-planner-digest-epoch-20261126`.
- Source path: `src/ark/agency/planner_journal.py`; the PlannerJournal v1 schema and event/hash formats are unchanged.

## Finding and correction

PlannerJournal's digest verifier compared `hashlib.sha256` and `json.dumps` with mutable module-level original aliases. A joint replacement of both imported module aliases and both original function aliases could make the check self-consistent.

The verifier now captures the original `hashlib` module, SHA-256 function, `json` module and JSON serializer in one import-time tuple retained by a keyword-only default. It checks the aggregate epoch, both module identities, both original aliases and both live callable attributes before accepting digest operations.

## Regression coverage

- Joint replacement of the two modules, both original callable aliases and the aggregate epoch is rejected before either hostile callback executes.
- A synthetic dictionary `items()` callback attempts the same replacement reentrantly during JSON serialization; the post-serialization check rejects before the hash callback can execute.

## Scope and limits

This is local in-process dependency-identity hardening, not a sandbox or independently authenticated digest authority. PlannerJournal v1 DDL/schema, event fields, hash domain/encoding, CAS, transition/recovery semantics and public APIs are unchanged. The work does not prove fsync/power-loss durability or exactly-once external effects. No live user data, real backend, credentials, hardware, paid/external compute, Candidate generation/promotion, protected V2 evaluation, frozen-contract change, main merge or UI/frontend work occurred. PR #8 remains Draft/unmerged; ARK/JARVIS remains NOT_PASSED.
