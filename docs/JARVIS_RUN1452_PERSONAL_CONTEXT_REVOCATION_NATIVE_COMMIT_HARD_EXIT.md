# Run1452 — Personal Context revocation native-COMMIT hard-exit evidence

**Exact parent basis:** Draft PR #8, branch \`research/jarvis-foundations\`, HEAD
\`1cf7b725fcf3c32ff5ffd59bda04ef03d140324b\`. This child branch is based on
that exact parent and targets only PR #8.

## New test-only coverage

A spawned process opens the production
\`SyntheticContextRevocationLedger.revoke()\` path and exits immediately after
the native SQLite COMMIT returns, before the source-path recheck or digest
receipt can return.

Cold reconstruction must retain one exact scope-digest/time marker, preserve
schema v1 and SQLite quick_check, extend an independently retained empty
revocation prefix, and deny both direct \`assert_not_revoked\` and the higher
level \`review_fresh_nonrevoked_context\` projection. The test confirms that
the veto database and its extant SQLite sidecars do not contain the synthetic
owner, namespace, or Memory content.

## Evidence limits

This is a synthetic local privacy-veto regression. It does not prove
authenticated consent, physical erasure, independent custody, trusted time,
atomicity between the separate Memory and revocation SQLite files, or
revocation against an already-consumed downstream projection. The test never
exports context, invokes a model/tool/backend, sends a notification, or
grants deletion authority.

No production source, schema/DDL, public API, frozen contract, V2 evaluation,
Candidate, UI/frontend, or main branch is changed. No paid/external compute,
credentials, hardware, destructive operation, training, preflight, GPU query,
or protected evaluation is used. Exact-head CI is required; no PASS is claimed.
