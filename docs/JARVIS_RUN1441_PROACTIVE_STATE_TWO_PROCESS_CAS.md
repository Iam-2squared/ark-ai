# Run1441 — Proactive state cross-process CAS

**Scope:** test-only regression package on an isolated child branch. No production
code, SQLite schema, policy vocabulary, frozen contract, or runtime integration
is changed.

## Coverage added

- Two spawned processes initialize the same previously absent proactive-state
  database. Both must converge on the same valid schema and observe an empty
  ledger; neither may leak a raw SQLite create/lock failure.
- Two independent process-owned ledger instances race the genesis revision
  (\`expected_revision=0\`). Exactly one may commit the initial state; the other
  must receive the domain-level \`SyntheticProactiveStateConflict\`.
- Two independent process-owned ledger instances race the same persisted
  revision (\`expected_revision=1\`). Exactly one may advance the state to
  revision 2; the other must receive the domain-level conflict.

The observations are represented by SHA-256 digests; fixture plaintext is not
intended to enter the durable state. The test uses only local SQLite and Python
multiprocessing.

## Evidence boundary

This package tests local process-level serialization and revision CAS for the
synthetic proactive state ledger. It does **not** establish a trusted clock,
authenticated owner identity, consent, notification authorization, automatic
replay, scheduler/timer operation, external dispatch, power-loss durability,
or independently retained audit custody. \`SyntheticProactiveState\` continues
to report all authority flags as false.

**Work basis:** \`research/jarvis-foundations\` at
\`963e8e67c63b36a376208d29efe06e23cb87be7b\`.

**Validation:** exact-head CI is pending until the child pull request is opened.
