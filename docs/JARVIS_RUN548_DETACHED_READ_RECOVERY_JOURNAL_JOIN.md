# Detached READ journal ↔ recovery history bridge (Run548)

## Scope and exact source

- PR: [#8 (Draft, unmerged)](https://github.com/Iam-2squared/ark-ai/pull/8), branch `research/jarvis-foundations`.
- Implementation: `src/ark/agency/disconnected_read_recovery_journal_bridge.py`, introduced at commit `76a01149e0544629b853a30439fea8600b5f3f74`.
- Regression cases: `tests/test_detached_read_recovery_journal_bridge_run548.py`, introduced at commit `62898c8a19ad0ec9c61ea72e6216bec8b0a8d302`.
- This note describes source and authored cases; it does **not** assert an independent local pytest PASS, an exact-HEAD 6/6 CI GREEN, or authenticated field evidence.

## New read-only integration invariant

The bridge accepts a caller-provided, ordered mock READ DAG restart history, a `ReadJournalSnapshot` previously recovered from local SQLite, and an independently retained `ReadJournalWitness` (count + SHA-256 tip). It independently recomputes the existing journal v1 chain for **every** receipt and derives the hypothetical recovery schedule using the existing deny-only scheduler.

Every `SUCCEEDED` step must have exactly one same-request receipt with matching step ID, operation and result digest. All its predecessors' receipts must appear earlier in the journal. No `FAILED`, `RUNNING`, `UNKNOWN` or `NOT_STARTED` step may have an apparent successful receipt. Foreign requests, duplicates, absent successes, digest drift, changed witness count/tip, bool-for-int count, inconsistent dependencies and tampered row carriers fail closed.

The output is a digest-only `ReadRecoveryJournalReview`. It has four explicit always-denied flags: backend dispatch, external result proof, automatic replay, and independent custody. The result is checked after denied-authority getter callbacks and the mock recovery schedule is recomputed before return.

## Boundaries and outstanding work

- Existing SQLite schema and frozen Memory/Planner/V2/V3 contracts are unchanged. No real ToolBackend, file side effect beyond the temporary local SQLite fixture in tests, scheduler advancement, training, model download, credential, paid resource, protected evaluation or main merge is involved.
- The READ receipt v1 journal records input/result hashes but not authenticated registry-bound action identity, permission, consent, or a trusted clock. This bridge **must not** be treated as execution provenance.
- A caller-retained tip may only detect a rewrite when it was genuinely preserved outside the SQLite store. Coordinated changes to both witnesses are not detected; SQLite recovery and Planner state are not a cross-store atomic snapshot.
- COMMIT-UNKNOWN failures remain for manual verification, not automated reattempts.
- Next dependency: connect the read-only recovery view to immutable registry-bound `DisconnectedRegisteredFixture` evidence, with a separate retained action-to-fixture link and exact-head passing CI before broader integration.

**CI evidence:** the new source/test commits were pushed by the ordinary GitHub Contents path. Record per-run final job conclusions only after inspecting the six actual jobs.
