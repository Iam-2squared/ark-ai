# ARK Run1309 — exact Memory scope-field admission

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `b11a17c6c078d1b4675fa4f392a7810e17ba7cb5`.
- Branch: `research/run1309-memory-scope-exact-store-ingress-20261125`.
- Production change is limited to local Memory store ingress; the existing Memory v1 DDL, schema version, dataclasses, serialized rows/events and public method signatures are unchanged.

## Finding

The store already rejected string-subclass owner/namespace fields on `put` and deterministic identity construction, but `get`, `search`, `delete`, scoped `purge_expired`, and `events` accepted an exact `MemoryScope` whose identity fields were subclasses of `str`. That left read and destructive entry points with weaker identity admission than writes.

## Change and regression coverage

- One helper snapshots an exact `MemoryScope` and requires exact built-in `str` owner and namespace fields before store I/O or clock callbacks.
- Apply the same admission to get/search/delete/scoped purge/events and reuse it in deterministic ID validation.
- Parameterized synthetic tests cover both owner and namespace subclasses across all five store APIs.
- Each invalid call must fail before SQLite connection or clock access; the original valid row and event remain unchanged.

## Evidence boundary

This aligns store-entry validation with existing `put` behavior. It does not change the `MemoryScope` constructor, Memory v1 schema/DDL, event format, retention semantics or frozen contract. It is not authenticated storage, independent erasure, trusted time, fsync/power-loss evidence, or a filesystem security boundary.

Synthetic local SQLite only. No live personal data, external service, paid compute, Candidate, protected V2 evaluation, credentials, hardware, destructive operation, UI/frontend work or main merge. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no PASS is claimed before completion. PR #5/#8 remain Draft/unmerged and PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
