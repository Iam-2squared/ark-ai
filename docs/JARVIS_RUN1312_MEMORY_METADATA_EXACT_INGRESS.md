# ARK Run1312 — exact Memory metadata store ingress

## Exact basis

- Parent: Draft PR #490, branch `research/run1309-memory-scope-exact-store-ingress-20261125`.
- Exact parent work-basis HEAD: `2bb8fda90c6e0f154c049ca17a4771257fa096a1`.
- Parent PR #490 exact-head CI run [45431502329](https://github.com/Iam-2squared/ark-ai/actions/runs/45431502329) was GREEN 6/6 on its exact child head.
- Child branch: `research/run1312-memory-metadata-exact-ingress-20261125`.

## Finding

`MemoryWrite` snapshots metadata into a mapping proxy, but its constructor accepts `str` subclasses for metadata keys and values. The SQLite store previously copied that mapping without requiring exact built-in strings. A reflectively replaced metadata carrier could also be passed into the store after construction of the frozen dataclass.

## Change and regression coverage

- Require the already-snapshotted metadata carrier to be the exact `MappingProxyType` before reading it.
- Snapshot at most 64 entries and require exact built-in `str` keys and values before constructing the validated write, hashing, SQLite open, or clock access.
- Synthetic regressions cover a `str` subclass key, a `str` subclass value, and a reflectively replaced mapping whose methods must not be called.
- Invalid updates must fail before SQLite/clock callbacks and preserve the previously committed row.

## Scope and evidence boundary

Production change is limited to local `SQLiteMemoryStore.put` ingress. No Memory v1 DDL/schema version/dataclass/public signature/event format/retention policy change. The `MemoryWrite` constructor remains unchanged; the store rejects ambiguous inexact metadata carriers at its persistence boundary.

Synthetic local SQLite only. This is local input-integrity hardening, not authenticated storage, independent erasure, trusted time, fsync/power-loss durability, cross-store atomicity, or exactly-once external effects. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no PASS is claimed.

No paid/external compute, Candidate, protected V2 evaluation, credentials, hardware, destructive action, UI/frontend work, frozen-contract change, or main merge. PR #5/#8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
