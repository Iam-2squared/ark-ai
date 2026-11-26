# Run1442 — Personal Context replay cross-process CAS

**Scope:** test-only child PR. No replay-ledger production code, SQLite schema,
privacy policy, frozen contract, disclosure authority, or runtime integration
is changed.

## Coverage added

- Two spawned processes construct independent read-only ledger objects and
  race the same request against the same retained genesis witness. Exactly one
  reservation may commit; the other receives a domain-level conflict.
- Two spawned processes race different request identities against the same
  genesis witness. Exactly one may commit. The loser must not auto-refresh or
  retry; a later explicit cold readback provides the new prefix for a separate
  reservation.
- Successful receipts remain denial-only for consent, revocation freshness,
  context disclosure, tool dispatch, and automatic replay. Fixture plaintext
  is not stored in the replay database.

## Evidence boundary

This is process-level SQLite reservation evidence for synthetic context
identities. It does not authenticate the owner, prove consent or current
revocation, authorize disclosure, enable retention, establish independent
custody, or provide cross-store atomicity with Memory or Action Audit.

**Work basis:** parent Draft PR #8 branch research/jarvis-foundations at
963e8e67c63b36a376208d29efe06e23cb87be7b.

**Validation:** exact-head CI is pending until this child PR is opened.
