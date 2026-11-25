# Run1429 — PlannerJournal digest dependency epoch on latest foundation

## Exact basis

- Parent Draft PR #8 branch: `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `c6ee53c5e5671b926b7625da7a7b5dfdd41ae7d3`.
- Rebased from Draft PR #613, branch `research/run1424-planner-digest-epoch-20261126`, exact child HEAD `e9e773633c531284730828cb688aa2bcbbf3ff40`.
- Parent source blob before reapplication: `4f8cc62d2adb31603bbb436df8ff87d6cf3ac4fd`; identical to the source base used by the predecessor child.
- Source: `src/ark/agency/planner_journal.py`; regression module: `tests/test_planner_journal_digest_vector_epoch_run1398.py`.

## Change

Retains the original `hashlib` module, SHA-256 callable, `json` module, and JSON serializer in one import-time epoch captured by a keyword-only verifier default. The verifier checks the aggregate epoch, module aliases, original callables, and live callable attributes before digest operations.

## Regression coverage

- Joint replacement of both modules, both original callable aliases, and the aggregate epoch is rejected before hostile callbacks execute.
- A synthetic dictionary `items()` callback attempts replacement during serialization; the post-serialization guard rejects before the hash callback executes.

## Scope and evidence limits

PlannerJournal v1 DDL/schema, event fields, hash domain/encoding, CAS, transition/recovery semantics, and public APIs are unchanged. This is local in-process dependency-identity hardening, not a sandbox or independently authenticated digest authority. It does not prove fsync/power-loss durability or exactly-once external effects.

No live data, real backend, credentials, hardware, paid/external compute, Candidate generation/promotion, protected V2 evaluation, frozen-contract change, main write/merge, or UI/frontend work occurred. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no production-readiness or ARK/JARVIS PASS is claimed.
