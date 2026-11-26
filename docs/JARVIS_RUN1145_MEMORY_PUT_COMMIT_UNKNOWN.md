# Run1145 — Memory put COMMIT acknowledgement ambiguity

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Parent work-basis HEAD: `243a65a121690bb0fc1f4a0596b9d1397da79c3c` (after the exact-head-GREEN proactive-state COMMIT-outcome test was integrated).
- Child branch: `research/run1145-memory-put-commit-unknown`.
- Test: `tests/test_memory_put_commit_unknown_run1145.py`.

## Coverage

A subprocess installs a stable SQLite connection factory before importing ARK, then injects a lost acknowledgement at the native connection context-manager boundary for `SQLiteMemoryStore.put`.

The four synthetic cases cover:

- create with native rollback before the acknowledgement is lost;
- create with native COMMIT followed by a lost acknowledgement;
- update with native rollback before the acknowledgement is lost;
- update with native COMMIT followed by a lost acknowledgement.

Every case requires the public `put` call to raise and exactly one COMMIT-boundary attempt. A cold store then reads the persisted row and event prefix:

- rollback preserves the previous row/event prefix (or no row for a create);
- durable COMMIT exposes exactly one new row revision and matching event;
- stale genesis/revision CAS is rejected after a durable write;
- no automatic retry occurs, and event representations contain no fixture content or metadata.

## Evidence boundary

This is a synthetic local SQLite transaction-boundary regression. It is not power-loss/fsync durability, independent storage custody, authenticated writer provenance, trusted time, consent, physical erasure, cross-store atomicity, or exactly-once external effects. A lost COMMIT acknowledgement remains UNKNOWN until explicit cold readback; the test does not authorize automatic retry.

No production source, Memory v1 DDL/public API, frozen contract, V1/V2 evidence, UI, PR #5, PR #9, or main branch is changed. No paid/external compute, Candidate generation/promotion, protected V2 evaluation, credentials, physical hardware, or external dispatch is used.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no local pytest/Ruff PASS is claimed. ARK/JARVIS remains NOT_PASSED.
