# ARK Run1352 — Exact Memory metadata store ingress

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `d8079f8b96bfa0875e0ad77372088b003e1c6550`.
- Child branch: `research/run1352-memory-metadata-exact-ingress-20261125`.
- Production file: `src/ark/memory/sqlite_store.py`.
- Regression module: `tests/test_memory_metadata_exact_store_ingress_run1352.py`.

## Finding and correction

The frozen `MemoryWrite` constructor intentionally remains compatible with `str` subclasses and snapshots metadata into a mapping proxy. The durable SQLite store previously copied that mapping without requiring exact built-in string keys and values. A reflectively replaced metadata carrier could also reach mapping callbacks before the store rejected it.

The store now requires the exact mapping-proxy carrier, bounds it to 64 entries, and snapshots only exact built-in `str` keys and values before reconstructing the validated write, serializing, hashing, opening SQLite, or sampling the clock.

## Regression coverage

- String-subclass metadata keys and values are rejected before SQLite and clock callbacks.
- A reflectively replaced hostile mapping is rejected by exact carrier type without invoking `__len__`, iteration, `items()`, or item access.
- Previously committed row contents remain unchanged after denial.

## Scope and evidence boundary

No Memory v1 DDL/schema version/dataclass/public signature/event format/retention policy change. The frozen `MemoryWrite` constructor and `MemoryScope` contract are unchanged. This is local input-integrity hardening, not authenticated storage, independent erasure, trusted time, fsync/power-loss durability, cross-store atomicity, or exactly-once external effects.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS or CI PASS is claimed. Synthetic local SQLite only; no live personal data, paid/external compute, Candidate, protected V2 evaluation, credentials, hardware, destructive operation, frozen-contract change, main merge, or UI work occurred. PR #5 and PR #8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
