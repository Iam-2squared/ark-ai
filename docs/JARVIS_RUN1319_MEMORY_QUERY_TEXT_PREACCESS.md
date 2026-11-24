# ARK Run1319 — exact Memory query text before SQLite ingress

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD after integrating the GREEN Run1317 child PR #498: `77d3b2f50d258bb3694afc0d03830e0d44644961`.
- Child branch: `research/run1319-memory-query-preaccess-20261125`.
- Run1317 PR #498 exact-head CI [45453681591](https://github.com/Iam-2squared/ark-ai/actions/runs/45453681591) was GREEN 6/6 before its squash integration into PR #8. This is parent evidence only and does not validate Run1319.

## Finding and change

The frozen `MemoryQuery` v1 constructor intentionally accepts `str` subclasses. `SQLiteMemoryStore.search()` already rejected a non-exact query-text carrier, but its first query-epoch check ran only after `_connect_readonly()` opened SQLite. An invalid caller carrier could therefore reach private-store access before rejection.

The store now validates the complete query epoch before opening SQLite. Its phase diagnostic now says “during read”, which is accurate for the pre-I/O and later snapshot checks. No query text callback is needed for the exact-type denial.

## Regression coverage

- Construct a valid frozen `MemoryQuery` with a synthetic `str` subclass.
- Replace SQLite connection and expiry-clock entry points with fail-fast sentinels.
- Require the store to reject the query before either sentinel or any subclass `strip` / equality callback runs.
- Confirm a normal exact built-in string query still returns the expected empty result on the same local store.

## Scope and evidence boundary

One local Memory search preflight fix and a synthetic regression. No Memory v1 DDL/schema/dataclass/public signature/event format/retention or frozen contract changes. Synthetic local SQLite only; no live data or external backend. This does not establish fsync/power-loss durability, cross-store atomicity or external exactly-once effects.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. PR #5/#8 remain Draft/unmerged; PR #9 remains untouched. No paid/external compute, Candidate, protected V2 evaluation, credentials, hardware, destructive operation, UI work or main merge.
