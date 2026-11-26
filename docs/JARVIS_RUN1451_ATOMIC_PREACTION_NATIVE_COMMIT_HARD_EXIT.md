# Run1451 — atomic pre-action native-COMMIT hard-exit evidence

**Exact parent basis:** Draft PR #8, branch \`research/jarvis-foundations\`, HEAD
\`1cf7b725fcf3c32ff5ffd59bda04ef03d140324b\`. This child branch is based on
that exact parent and targets only PR #8.

## New test-only coverage

A spawned process opens the production
\`DisconnectedAtomicPreactionLedger.reserve()\` path and exits immediately
after the underlying SQLite connection context returns from native COMMIT,
before connection close or the retained witness can be returned.

Cold reconstruction must verify:

- exactly one intent row and one matching digest-only pre-action audit row;
- schema v1 and SQLite quick_check remain valid;
- the committed occurrence is visible from a same-file diagnostic witness;
- a stale genesis witness cannot append another occurrence;
- the same occurrence cannot be reserved again using the local tip;
- all dispatch, automatic replay, external-effect, trusted-approval and
  independent-custody authority flags remain false.

## Evidence limits

This is a synthetic local SQLite process-exit regression. The retained witness
is derived from the same database and is not independent custody or an
authenticated approval. The test does not prove fsync/power-loss durability,
trusted time, human consent, cross-store atomicity, a real backend effect, or
exactly-once external execution. No backend is invoked and no automatic retry
is introduced.

No production source, schema/DDL, public API, frozen contract, V2 evaluation,
Candidate, UI/frontend, or main branch is changed. No paid/external compute,
credentials, hardware, destructive operation, training, preflight, GPU query,
or protected evaluation is used. Exact-head CI is required; no PASS is claimed.
