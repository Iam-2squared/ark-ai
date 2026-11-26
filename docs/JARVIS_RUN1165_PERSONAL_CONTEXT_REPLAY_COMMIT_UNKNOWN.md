# Run1165 — Personal Context replay reservation COMMIT ambiguity rebase

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent HEAD at branch creation: `c12bd530bceacaea47122a9a9010d3a3b5fd6245`.
- Rebased the test-only native-COMMIT acknowledgement-loss regression from Draft PR #331 exact child HEAD `a1530cd985d63b08c189ad93e8ed123c63115190`.
- Source exact-head CI [45104098448](https://github.com/Iam-2squared/ark-ai/actions/runs/45104098448) was GREEN on the source head only; it does not transfer to this rebase.
- New branch: `research/run1165-personal-context-replay-commit-unknown`.

## Change

The synthetic Personal Context replay ledger is exercised at both possible native SQLite outcomes when COMMIT acknowledgement is lost: rollback before acknowledgement and successful native COMMIT before acknowledgement. In both cases the reservation is attempted exactly once, no receipt is returned, and a fresh ledger instance determines the persisted outcome by cold readback. A committed row makes the retained witness stale and the request a duplicate; a rolled-back transaction leaves the genesis witness and no row. Only digest identifiers are stored; synthetic context text is not persisted.

No production Personal Context code, schema/DDL, request identity, retention, revocation, consent, or disclosure policy changes.

## Evidence boundary

Synthetic fixtures and disposable local SQLite only. This does not prove fsync/power-loss durability, independent storage custody, trusted time, consent, revocation freshness, disclosure authority, cross-store atomicity, or exactly-once external effects. A local COMMIT error is resolved by cold readback; it is not permission for automatic replay.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No paid/external compute, Candidate generation/promotion, protected V2 evaluation, credentials, hardware, UI/frontend work, frozen-contract change, destructive action, or main merge is included. PR #8 and PR #5 remain Draft/unmerged; PR #9 remains untouched; ARK/JARVIS remains NOT_PASSED.
