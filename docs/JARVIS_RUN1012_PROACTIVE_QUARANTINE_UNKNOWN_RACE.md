# Run1012 — Proactive quarantine COMMIT-UNKNOWN and competing-process race

## Scope

Test-only, free/local work on the existing disconnected schedule quarantine ledger.

- Simulate a lost SQLite COMMIT acknowledgement after the native COMMIT has actually succeeded.
- Require the call to raise without returning a receipt; cold readback sees exactly one durable quarantine row.
- Verify the pre-commit witness is stale after restart and cannot append the same expired occurrence again.
- Race two independent Python processes from the same retained witness against the same expired slot. Exactly one process may commit; the other must fail closed after acquiring the SQLite writer slot.
- Verify the resulting one-row history with SQLite `quick_check`, then perform only a same-database diagnostic inspection using a witness reconstructed from that same local database.

## Safety and interpretation

All policy values, timestamps, occurrences, and SQLite files are synthetic and disposable. No live schedule, OS timer, notification, ToolBackend, consent, trusted clock, external action, or user data is involved.

A post-COMMIT exception is an **unknown caller outcome**, not proof of rollback. The test requires no automatic retry: the old witness remains stale and the persisted occurrence remains unique. A locally reconstructed witness is explicitly not independently authenticated.

The process race checks local SQLite serialization and append uniqueness only. It does not establish cross-store atomicity, filesystem custody, power-loss durability, authenticated provenance, or exactly-once external effects. Quarantine remains an overdue classification only; execution, notification, consent, trusted-clock, and automatic-replay flags remain false.

No production source, frozen contract, UI/frontend code, Candidate artifact, model, paid service, external compute, credential, protected V2 evaluation, or main branch is changed.
