# Run1411 — Memory generation CAS absent-hook custody

Status: isolated hardening of the opt-in local generation-CAS path under Draft PR #8. No Memory or roadmap PASS is claimed.

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `43eaf52c81b86ed8cdca7e18b6abea0eee3dcdfe`.
- Child branch: `research/run1411-memory-generation-absent-hook-custody-20261125`.
- Scope: `src/ark/memory/generation_fenced_cas.py` and one synthetic SQLite regression file.

## Finding

The generation token, `MemoryScope` and `MemoryWrite` validators retained hook vectors with `vars(type).get(name)`. For class hooks absent from the class namespace, the retained value was `None`; installing explicit `None` later therefore remained indistinguishable from true absence. The token/input vectors and their paired aliases also lacked one retained epoch binding their exact type objects and vector objects.

## Change

- Capture a unique absent-class-hook sentinel and use it when retaining token, scope and write hook vectors.
- Require namespace absence for sentinel-backed entries; require exact descriptor identity for present entries.
- Retain exact token/input type aliases, field vectors, hook vectors, denial descriptors and the sentinel in import-time epochs captured by validator defaults.
- Reject sentinel rebinding, coordinated vector replacement and coordinated type-alias replacement before token/input field access or SQLite connection.
- Keep existing token denial semantics, input field semantics, generation CAS row/event digest rules, expiry/CAS behavior and post-COMMIT readback unchanged.

## Regression coverage

- Explicit `None` and exact-sentinel installation are rejected for `__new__`, `__getattribute__` and `__getattr__` on the token, scope and write carriers.
- All `__new__` allocation-slot probes run in isolated subprocesses to prevent CPython type-slot residue in the main pytest process.
- Sentinel rebinding, joint token/input hook-vector replacement and joint type-alias replacement are rejected.
- Each rejection asserts SQLite is not opened and the original row/event state remains unchanged.
- Fixtures use only a throwaway local SQLite database and synthetic values.

## Evidence boundary

The opt-in generation-CAS token remains non-authorizing: it is not consent, a writer identity, trusted time, a capability or permission for external effects/replay. This does not establish independent custody, cross-store atomicity, fsync/power-loss durability or exactly-once external effects.

Frozen Memory v1 put/delete APIs, SQLite schema, MemoryScope/MemoryWrite definitions and frozen contracts are unchanged. No paid/external compute, paid service, Candidate generation/promotion, protected V2 evaluation, credentials, account connection, hardware action, destructive operation, main write/merge or UI/frontend work occurred. PR #5/#8/#9 remain Draft/unmerged; PR #9 remains untouched.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff result or PASS is claimed.
