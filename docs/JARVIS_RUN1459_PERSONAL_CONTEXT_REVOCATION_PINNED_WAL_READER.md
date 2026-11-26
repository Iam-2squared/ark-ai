# Run1459 — Personal Context revocation COMMIT with a surviving WAL reader

**Parent:** Draft PR #8, branch `research/jarvis-foundations`.
**Exact parent work-basis HEAD:** `6f78206e68b2c9b2799f77af29d51f6a4ddcca4c`.
**Child:** `research/run1459-personal-context-revocation-pinned-wal-reader-20261126`.

## Scenario

The test creates synthetic Memory content and an empty production `SyntheticContextRevocationLedger`, explicitly enables WAL mode for the veto database, and pins an independent read-only snapshot of the empty revocation table. A spawned writer calls the production `revoke()` path and exits immediately after native SQLite COMMIT returns, before the source-path recheck, digest receipt, or connection cleanup.

The pinned reader must continue to see the empty pre-revocation prefix. A TRUNCATE checkpoint must remain incomplete while it is open. After last-reader close, cold reconstruction must recover exactly one scope-digest/time marker, direct `assert_not_revoked` must deny, and the higher-level `review_fresh_nonrevoked_context` projection must deny before returning Memory content. The final checkpoint, schema-v1 check and quick_check must succeed.

The veto database and extant WAL/SHM files must not contain the synthetic owner, namespace, or raw Memory content.

## Scope and evidence limits

Test-only synthetic local SQLite evidence. No production source, schema/DDL, public API, frozen contract, consent flow, Memory deletion, or external context export changes.

This composes native-COMMIT process-exit with a surviving WAL reader and last-reader checkpoint behavior. It does **not** prove authenticated consent, physical erasure, independent custody, trusted time, atomicity between the separate Memory and revocation databases, revocation against an already-consumed downstream projection, power-loss durability, notification/dispatch authority, or exactly-once external effects. The revocation marker remains a local negative-use veto only.

No paid/external compute, credentials, hardware, Candidate, protected V2 evaluation, main write/merge, or UI/frontend work occurred. PR #8 remains Draft/unmerged. Fresh exact-head CI is required; no PASS is claimed.
