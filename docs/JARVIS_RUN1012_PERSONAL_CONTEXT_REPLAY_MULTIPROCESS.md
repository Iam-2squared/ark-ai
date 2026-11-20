# Run1012 — Personal Context replay reservation across processes

## Scope

Test-only, free/local extension of the Personal Context replay reservation ledger.

- Two independent Python processes open the same existing empty local SQLite ledger.
- Both build the same deterministic, hash-only request binding and retain the same genesis witness.
- A barrier releases both processes to reserve the same request identity concurrently.
- Exactly one reservation may commit; the other must fail closed on the stale witness or duplicate identity.
- Cold readback verifies one contiguous row, SQLite integrity, unchanged history after stale retry, and no raw fixture payload in the database file.

## Safety and interpretation

All owner/scope/record/request identifiers and content are synthetic. The ledger stores request identity and digests only; no real context is loaded, disclosed, summarized, sent to a model, or dispatched to a ToolBackend.

This extends the existing same-process thread race to independent processes and validates the SQLite writer-slot CAS boundary. It does not establish independent custody, filesystem ownership, power-loss durability, consent, revocation freshness, or exactly-once external effects. A replay receipt remains reservation metadata only.

No production source, frozen contract, UI/frontend code, Candidate artifact, paid service, external compute, credential, protected V2 evaluation, or main branch is changed.
