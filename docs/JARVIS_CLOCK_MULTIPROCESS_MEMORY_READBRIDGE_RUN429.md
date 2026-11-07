# ARK JARVIS Run429 — Clock Carrier, Multiprocess Memory Snapshot and Four-Store READ-Bridge Fault Matrix

**Scope:** isolated, reversible, offline/disconnected/synthetic-only foundation changes on `research/jarvis-foundations` (Draft PR #8). **NOT** a JARVIS PASS, external action authorization, authenticated time, cross-file atomicity or external exactly-once execution. No physical PC, real sensor, paid API, external GPU, protected evaluation, real Candidate, credential, private connector or actual ToolBackend action was used.

## Coherent packages and test intent

### Package 1 — Clock witness constructor carrier integrity

- Source: `src/ark/agency/synthetic_clock_sequence_review.py`; source commit `17374bc2711e9731b3b0f42be82198603be73f2f`.
- Regression: `tests/test_synthetic_clock_constructor_carriers_run429.py`; source+tests commit `293a37103baec1002acde36051a7a29168108f89`.
- A reflectively substituted `SyntheticClockWitness.__init__` can build an exact-type, equal-value but *distinct-string-carrier* `source_digest` or `chain_hash`. In addition to the original field-value checks, the sequence now requires the constructed witness to retain the exact source carrier sampled from the untrusted input and the exact freshly calculated chain-hash carrier.
- The two negative cases must raise `SyntheticClockRejected`. The clean fixture remains deterministic and explicitly denies `trusted_clock_verified`, `dispatch_authorized` and `automatic_replay_authorized`.
- Limit: string object identity and local digests are only test-time integrity fences, **not** authenticated clock origin, signed issuer identity or cryptographic authority.

### Package 2 — Separate-process Memory v1 coherent namespace snapshot

- Regression: `tests/test_memory_cross_process_snapshot_epoch_run429.py`; commit `f5c9fc2f45d7d20b051f114353291823644bdff8`.
- At the moment the reviewer reaches its single untrusted clock sample, a distinct local Python process commits sequential inserts or updates in *both* namespaces. This occurs **after** the reviewer has anchored its SQLite read-only transaction.
- Both parameter cases require the original coherent witness to contain the old records in *both* namespaces; a fresh independent read must see the newer committed rows and a different content-free provenance digest. No content is sent over a network.
- This exercises WAL reader/writer snapshot isolation, not a claim of multi-database atomicity or of a globally current snapshot. The v1 schema and `CoherentSnapshotRequest` public API are unchanged.

### Package 3 — Dependent WRITE through a READ bridge with four-store retained-tail loss

- Regression: `tests/test_recovery_read_bridge_four_store_loss_run429.py`; commit `b932ad848fdc6295d0cce5bee8da1b8d4e876a13`.
- Plan graph: `upstream WRITE -> bridge READ -> downstream WRITE`. The upstream has a synthetic crash after durable audit-link logging (locally RUNNING); the downstream is locally PENDING with an independently persisted one-shot occurrence reservation.
- Capture an independently retained plan tail, occurrence ledger witness, audit continuity witness, and occurrence–audit link witness. Prove the untouched cloned set matches before fault injection.
- Delete only the *last committed row* from **one disposable cloned SQLite source at a time**: `synthetic_plan_events`, `synthetic_occurrence_reservations`, `action_events`, or `synthetic_occurrence_audit_links`.
- The retained cross-store read must reject each one-source tail loss, never call the mock backend, and never promote RUNNING/reserved PENDING into automatic retry. The untouched original source must still reproduce its prior read-only diagnosis.
- Limit: four SQLite files have separate commits; independent retained witnesses catch tested history loss but do not manufacture a shared atomic snapshot or attest whether an external effect occurred.

## Validation and free-only gates

These source/tests were saved through the normal GitHub Contents API; the repository's existing test matrix was triggered automatically. This document records the *required checks*, not a fabricated claim that asynchronous CI has completed.

Required test matrix: Ubuntu and Windows, Python 3.11/3.12/3.13, Ruff plus repository pytest. Focused suites:

```text
tests/test_synthetic_clock_constructor_carriers_run429.py
tests/test_memory_cross_process_snapshot_epoch_run429.py
tests/test_recovery_read_bridge_four_store_loss_run429.py
```

Check every relevant run ID/commit SHA and its jobs separately; keep any historical FAIL as FAILED. Do not equate a predecessor HEAD's GREEN with this HEAD. No duplicate manual workflow runs.

**Hard boundaries:** PR #5 remains Draft/NOT_PASSED, V3 Contract 1 frozen, V1/V2/Local UI/Launcher and frozen Memory v1/ActionAudit v1 SQL unchanged. No merge, real executor, actual consent/issuer verification, live time source, camera, mic, notification, real Candidate adapter/weights, training or paid compute. UNKNOWN/RUNNING and reserved PENDING WRITEs remain held against auto-replay.

**Next:** independently confirm the final exact-head CI; if tests fail, preserve failure evidence and use the smallest normal, safety-preserving Contents change. Further work should prioritize multi-store forensic prefix matrices and process-independent Memory CAS/expiry evidence, then privacy and deny-only Issuer/Clock contracts, keeping execution disabled.
