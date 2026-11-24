# ARK Run1317 — exact Memory scope fields before SQLite ingress

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `824bb987f0addf4e961c9f4949f6075ca42a1caa`.
- Child branch: `research/run1317-memory-scope-exact-store-ingress-rebase-20261125`.
- Previous child exact-head CI [45431502329](https://github.com/Iam-2squared/ark-ai/actions/runs/45431502329) was GREEN on its old base only; it does not transfer to this rebase.

## Finding and change

The store already rejected `str` subclasses for owner/namespace on writes and deterministic ID construction, but read/delete/purge/event entry points accepted them inside an exact `MemoryScope`. A shared helper snapshots exact built-in string identity fields before SQLite or clock access across get/search/delete/scoped purge/events.

## Scope and evidence boundary

One local Memory implementation hardening change with synthetic regressions. No Memory v1 DDL/schema/dataclass/public signature/event format/retention or frozen contract changes. No live data or external backend.

Synthetic local SQLite only. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No paid/external compute, Candidate, protected V2 evaluation, credentials, hardware, destructive action, UI/frontend work, frozen-contract change or main merge. PR #5/#8 remain Draft/unmerged; PR #9 remains untouched.
