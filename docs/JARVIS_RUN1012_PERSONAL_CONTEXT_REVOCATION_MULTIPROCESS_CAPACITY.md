# Run1012 — Personal Context revocation capacity across processes

## Scope

Test-only, free/local extension of the synthetic Personal Context revocation ledger.

- Start two independent Python processes from the same empty local SQLite ledger.
- Configure both processes with a one-row test capacity and release them together to revoke different synthetic scopes at the same timestamp.
- Require exactly one committed veto and one explicit capacity-exhausted denial.
- Cold-reopen the ledger, verify the one-row retained history and SQLite integrity, and prove the winner remains vetoed while the other scope is not collapsed into the same identity.
- Verify the database contains only scope digests and timestamps, not raw owner or namespace strings.

## Safety and interpretation

All scope identifiers and timestamps are synthetic. Only disposable local SQLite is used. No live personal data, external connector, consent, model, ToolBackend, disclosure, deletion, or erasure operation occurs.

The test extends the existing thread-level capacity race to independent processes. It checks the `BEGIN IMMEDIATE` writer-slot capacity invariant; it does not prove filesystem custody, power-loss durability, authenticated provenance, cross-store atomicity, or consent. Absence of a veto remains not evidence of permission.

No production source, frozen contract, UI/frontend code, Candidate artifact, paid service, external compute, credential, protected V2 evaluation, or main branch is changed.
