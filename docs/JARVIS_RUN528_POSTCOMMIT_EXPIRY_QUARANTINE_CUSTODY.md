# Run528 — Post-COMMIT WRITE custody, expiry row/event coherence, scheduler quarantine

**Scope:** reversible, disconnected, free-only JARVIS foundations in PR #8, `research/jarvis-foundations`. No change to the frozen agency/memory v1 contracts, V1/V2/Local UI/Launcher evidence or main. **ARK/JARVIS overall NOT_PASSED.** This record is a source-grounded design/test inventory, not an assertion that a later CI HEAD passed.

## Work packages

### 1. Durable synthetic WRITE reservation: last-callback / persisted witness fence

- Implementation: `src/ark/agency/disconnected_write_slot_ledger.py`; initial source commit `a91a6b088249ff194c6a33ad4e5fd37cd96d3fd4`; tests `tests/test_write_slot_final_postcommit_epoch_run528.py`, combined package `a8d82ba0d9b644c7281ae144960139f5a6e43875`.
- After the SQLite COMMIT, the final receipt denial callbacks are revisited as untrusted/reentrant. Exact result fields, witness tuple/identity, retained input and denied authority-property descriptor identities must remain unchanged.
- Open the same ledger path read-only AFTER the final callback and recompute SQLite reservation chain witness. A changed database, altered receipt or failed reopening is a denial, **not rollback, automatic retry or external exactly-once proof**.
- Seven new synthetic cases (4 carrier mutations, 1 on-disk post-COMMIT mutation, 1 class descriptor mutation, 1 normal restart/no-replay).

### 2. Memory expiry: read-only candidate and event reconciliation

- Implementation: `src/ark/memory/expiry_candidate_preview.py`; source `27e7c5570bb3c1e4b99f36156d45f0ddd47b48c1`; tests `tests/test_memory_expiry_event_alignment_run528.py`, combined `5f0ed7d4e5f0d4acbb3d599e2bb909d6ed42c652`.
- A selected expiry row is not accepted solely because its live-record hash and expiry time appear valid. In the **same SQLite read transaction**, inspect the latest matching `memory_events` row and require identical owner/namespace/revision plus the appropriate live `create` or `update` operation.
- Check the overflow/pagination `limit+1` row as well as visible rows. Review remains content-free and has no delete, clock, consent, or disclosure authority. This is a last-event consistency check; it is **not authenticated historical provenance**.
- Six new cases (4 persisted event mutations, 1 hidden page boundary, 1 valid CAS update and retained verification).

### 3. Scheduler: post-COMMIT overdue quarantine cannot mint authority

- Implementation: `src/ark/disconnected_schedule_quarantine_ledger.py`; source `89825b17c04056de468cba4128a887d96d0e7444`; tests `tests/test_schedule_quarantine_postcommit_denial_run528.py`, combined package `2031de2195c9f411e3d0eec15f1ef01cdffb92a5`.
- The expired synthetic slot is already durably classified, but its returned receipt must deny execution, notification, replay, trusted clock and consent. False-valued callbacks are not trusted; they cannot change the receipt witness, source, policy or class-level denial descriptor.
- Reopen the local quarantine ledger read-only and verify the chain following those callbacks. Reject any mismatch **without making a second reservation or dispatching anything**.
- Eleven synthetic cases (5 forged authority flags, 2 changed witness/policy carriers, 1 changed persisted journal, 1 descriptor swap, 1 successful restart/no-dispatch).

## Evidence rules / limits

- **24 newly authored pytest cases = 7 + 6 + 11**. Their existence is not an independent pytest PASS or exact-head GREEN claim.
- Source/test commits on PR #8 trigger independent six-environment GitHub Actions runs. Each run applies **only** to its own `head_sha`; do not reuse earlier GREEN after later commits, including this documentation commit.
- Nothing here proves authenticated owners, a trusted monotonic clock, cross-store atomicity, real external side effects, or exactly-once external delivery. No ToolBackend, camera, microphone, API, GPU, payment, Candidate, protected V2 evaluation, PR merge or irreversible operation is authorized.
- Conservative continuation: inspect exact-head CI; fix only observed tests/lint without weakening refusals; then advance Planner/READ restart consistency, memory CAS/snapshot/witness durability, and scheduler occurrence/replay fences on independent free-only paths.
