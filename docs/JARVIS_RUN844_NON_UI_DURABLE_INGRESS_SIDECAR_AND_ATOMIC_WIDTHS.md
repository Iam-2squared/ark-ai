# ARK non-UI foundation — Run844 durable ingress and SQLite sidecar controls

Status at report creation: **implementation and regression fixtures saved on Draft PR #8; exact final HEAD six-job CI not yet established.** This is a technical work/evidence record, not an execution authorization, model-evaluation PASS, or frozen-contract amendment.

## Scope and provenance

Initial inspected PR #8 HEAD: `c280d2a66036da529cfb07ea482c93a33cd969bb` (Run843 checkpoint). Prior exact-HEAD [CI #43412325605](https://github.com/Iam-2squared/ark-ai/actions/runs/43412325605) completed **GREEN 6/6** for Windows/Ubuntu × Python 3.11–3.13. Draft PR #5 remained protected/unmerged and paused UI Draft PR #9 was not modified.

This invocation saved **four independent non-UI source + fixture packages**. The reported cases are authored parametrizations, **not** verified test passes at this document's creation. All test stores are disposable fixture databases; no physical PC, live ToolBackend, notification, media source, or paid service is accessed by the code paths introduced here.

### 1. Proactive expiry quarantine storage: path aliases and bounded SQL history

- Source [`11cb1841`](https://github.com/Iam-2squared/ark-ai/commit/11cb1841b7b4d76ee2f85961d3fcf7a42bcf304f); 14 parameterized regression cases [`24553b88`](https://github.com/Iam-2squared/ark-ai/commit/24553b88cccf683d3f4bdd182abfd0993e1d430d).
- Existing `_path` already refused aliased main SQLite paths. It now also rejects a non-regular, hardlinked or orphan `-wal`, `-shm` or `-journal` pathname before the SQLite open. The regular single-link sidecar case remains allowed; the routine does **not** remove or rewrite orphan bytes.
- An invalid historical `policy` table with multiple different policy rows is now rejected after fetching **at most two** rows, rather than materializing an arbitrarily large tuple. Valid one-row behavior remains identical.
- Exact SHA and synthetic slot widths are required **before** regexp matching for policy inputs, retained witnesses, durable chain history, and overdue occurrence claims. Bad/oversized fixture input is rejected before the storage write. The original digest/retained witness contracts and denial-only receipt flags remain unchanged.
- These are **lexical lstat preflights** and one SQLite snapshot, not atomic descriptor-relative path custody. Races between checks and SQLite file opens, concurrent last-close WAL/SHM unlink and authenticated scheduler time remain unsolved. Do **not** use them as authorization for real notifications or actions.

### 2. Deterministic Memory ID direct entry: original input budget

- Source [`4f04b718`](https://github.com/Iam-2squared/ark-ai/commit/4f04b718b07ce9fd00a6e7d399197e047ecb0fa4); 14 regression cases [`d3e43b37`](https://github.com/Iam-2squared/ark-ai/commit/d3e43b373fbef5ef4c2e2fe15c2ff08c3dad2c00), with fixture literal correction [`66e6c69b`](https://github.com/Iam-2squared/ark-ai/commit/66e6c69b6b6647eaaab0268795b9015166bdbce9).
- `deterministic_memory_id` is exported and can be called *without* the `MemoryWrite` constructor, bypassing its existing source-ID length limit. The direct function now enforces exact strings, a nonblank source of at most 512 code points, and original `MemoryScope` 256-code-point owner/namespace bounds before JSON allocation/hash.
- Reject a reflectedly mutated scope field or malformed UTF-8 surrogate before hashing a scope/source identity. Valid UTF-8 and ordinary bounded inputs retain the same deterministic canonical `mem_` digest bytes.
- Scope/source validation is only input hygiene. It is not a durable event anchor, independent provenance, trusted retention clock, or CAS transaction witness. Frozen Memory v1 DDL, events, and migrations are untouched.

### 3. Atomic disconnected pre-action ledger: bounded SQLite row hydration

- Source [`85e9b2b8`](https://github.com/Iam-2squared/ark-ai/commit/85e9b2b82f24507bc39f0add9501513ec23a508f); 16 regression cases [`c0c8e6a9`](https://github.com/Iam-2squared/ark-ai/commit/c0c8e6a98b1ef3b8bfbc599cd4c19f98fce7417d).
- Local synthetic identifiers now have fixed widths: `occ_` + 64 lowercase hex (68), `bound_` + 64 (70), and SHA-256 digest (64); checks run before regexp over a caller-controlled string. Exact module-level pattern identities remain pinned for synthetic validation.
- After checking existing schema in the same read transaction, count committed intents (maximum 128); use SQLite `typeof` and `length` predicates to reject BLOB, NULL or oversized identity/hash fields in both `intents` and `preaction_audit` **before** loading those rows into Python. Preserve the existing contiguous event chain/audit digest verification, retention witness equality/CAS, and atomic two-table write.
- The ledger is **inert and disconnected**; it has no ToolBackend execution method. A successfully committed local pre-action audit is neither durable approval provenance nor evidence of a real external effect. Unknown WRITE outcomes remain quarantined and never automatically replayed.

### 4. Privacy-safe Personal Context detached preview/replay ingress

- Source [`cfa285b1`](https://github.com/Iam-2squared/ark-ai/commit/cfa285b1680068d9fb01d8ff726bf016907e70e1); 15 parameterized tests [`d3a67d6e`](https://github.com/Iam-2squared/ark-ai/commit/d3a67d6efd150248cf97264481ee2236c64569a9).
- Require exact 64-character lowercase digest widths before regex for detached owner and allowed scopes, and private fixture content hashes; require exact 36-character `rec_` identity before regex.
- Reject an overlong retained report digest, owner label, record-ID tuple, or serialized private JSON **before** rebuilding its expected output from private fixtures. The original digest/scope equality and all four False-only authority descriptors are unchanged.
- Valid synthetic local previews and proof-of-replay remain **not** consent, external-export permission, live Memory access, or trusted time.

### CI-triggered test compatibility correction (Memory, without weakening checks)

- [#43420404165](https://github.com/Iam-2squared/ark-ai/actions/runs/43420404165) and [#43420615381](https://github.com/Iam-2squared/ark-ai/actions/runs/43420615381) surfaced a **real** incompatibility: the older corrupt-persisted-row fixture used the now-bounded public `deterministic_memory_id` helper to synthesize an intentionally oversized source ID. That helper now correctly refuses the invalid direct input before the test can create its deliberately malformed SQLite row.
- Minimal source repair [`b3569fed`](https://github.com/Iam-2squared/ark-ai/commit/b3569fed220e38d8b7217380c02d83744f0df1a6) preserves the original typed `MemorySchemaError` / `MemoryWrite bounds` diagnostic by rejecting an oversized *stored* source before calling the public helper during hydration.
- Existing test-only fixture correction [`4dbb5597`](https://github.com/Iam-2squared/ark-ai/commit/4dbb559785abe557b90b9bda1c3ee99ff62d44af) builds the **forbidden** hash-consistent SQLite row offline with canonical JSON and SHA, bypassing the valid public helper strictly for tamper testing. No production caller can use this as an allowed Memory write.
- The initial new test file also erroneously used a Python doubled backslash in its invalid-surrogate literals; [`66e6c69b`](https://github.com/Iam-2squared/ark-ai/commit/66e6c69b6b6647eaaab0268795b9015166bdbce9) corrected the synthetic test fixtures. Later [#43420615381](https://github.com/Iam-2squared/ark-ai/actions/runs/43420615381) Ubuntu tests show the surrogate cases no longer failing and isolate the remaining older fixture issue. These are not new privacy permissions or an API weakening.

**Authoring total: 59 new parameterized cases across four packages, plus one corrected existing tamper fixture.** These are authored counts, NOT exact-final-HEAD verified passes. The later corrections and this report have automatic CI pending; do not promote an earlier GREEN to their HEAD.

## Evidence and limitations

At initial report creation the new PR branch had ordinary automatic CI for new source and test commits: [#43420082795](https://github.com/Iam-2squared/ark-ai/actions/runs/43420082795), [#43420231231](https://github.com/Iam-2squared/ark-ai/actions/runs/43420231231), [#43420404165](https://github.com/Iam-2squared/ark-ai/actions/runs/43420404165), [#43420513668](https://github.com/Iam-2squared/ark-ai/actions/runs/43420513668), [#43420615381](https://github.com/Iam-2squared/ark-ai/actions/runs/43420615381), [#43420834111](https://github.com/Iam-2squared/ark-ai/actions/runs/43420834111), [#43420959518](https://github.com/Iam-2squared/ark-ai/actions/runs/43420959518); all were pending/in progress on last observation. **No latest-head 6/6 GREEN is claimed.** No local complete Ruff/pytest/GGUF run was made.

Relevant independent controls: `docs/DURABLE_STATE_INTEGRITY_CONTRACT.md`, `docs/AGENCY_EXECUTION_CONTRACT.md`, and `docs/JARVIS_EXECUTION_SAFETY_INTEGRATION_GATE.md`. This work does not amend them or frozen V1/V2/Local UI/Launcher evidence.

## Prioritized next free-only work

1. Inspect exact committed source/test CI; repair any actual lint/functional failures via normal Contents API, without relaxing denial behavior or rewriting newer work.
2. Reproduce WAL/SHM last-close alias races using disposable process fixtures, then separate the remaining TOCTOU path-custody limit from the diagnosed SQLite lifecycle.
3. Extend durable Memory COMMIT-UNKNOWN and Planner terminal/UNKNOWN recovery proofs; keep opaque internal receipts nonauthorizing and anti-replay.
4. Cross-check registry-bound ToolRegistry, exact PermissionGate and trusted audit-before-action with disconnected Mock Executor after each lower-layer HEAD has GREEN evidence.
5. Preserve all free-only, no new UI, no Candidate, no protected final evaluation, no real dispatch, no main merge boundaries.
