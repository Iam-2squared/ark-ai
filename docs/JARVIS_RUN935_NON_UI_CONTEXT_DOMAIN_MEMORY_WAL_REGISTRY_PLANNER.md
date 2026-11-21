# ARK AI Run935 — verified Personal Context digest, cross-process WAL, registry-bound inert audit, Planner CAS

**Recorded:** 2026-11-17T13:51:03.307+09:00 (Asia/Tokyo/JST reporting clock, **not** a trusted authorization/audit clock).  
**Basis:** Run934 checkpoint `5e13743b7e64101f59683a2b94bdc36d05e5802e` / [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8), `research/jarvis-foundations`.  
**Exact new test work HEAD:** `7d12eb020cd8591b9be5f8712529174a5d3054f4` (PR head independently read before this report).  
**Overall:** ARK/JARVIS **NOT_PASSED**. Zero-cost, offline/mocked non-UI verification only. No actual tool dispatch.

## Four independent work packages — 8 new cases plus correction of six existing cases

1. **Personal Context canonical NUL-domain regression repair** — [`3f846a72`](https://github.com/Iam-2squared/ark-ai/commit/3f846a72817e0668cc3a573947c033897c1cf1e2). Corrected `tests/test_personal_context_rehashed_detached_binding_run934.py` to use the actual protocol NUL delimiter via `bytes((0,))`, not a two-character escaped backslash-zero marker. Added a positive assertion that recomputing the digest of an *unmodified valid preview* matches production `local_digest`. Its existing **six** synthetic mutation cases now exercise the intended self-consistent rehash boundary rather than trivially failing a wrong digest domain. This is a **test fix**, not a production guard relaxation.
2. **SQLite Memory cross-process WAL reader and last-close** — [`322a273c`](https://github.com/Iam-2squared/ark-ai/commit/322a273c6d9a999fa7c0be4d41b9ae3824111610), `tests/test_memory_cross_process_wal_reader_last_close_run935.py`, **2 new parametrized cases** (read-only or read/write SQLite reader). An independent subprocess retains a coherent old row/event snapshot while a separate Memory store performs generation-fenced CAS. The cold reader must see the updated row/event pair, the old token must fail after concurrent write, and the committed pair must survive last reader close/reopen. Disposable SQLite and synthetic content only; subprocess barriers have bounded timeouts and cleanup.
3. **ToolRegistry + PermissionGate + disconnected atomic audit boundary** — [`f24e8eba`](https://github.com/Iam-2squared/ark-ai/commit/f24e8eba67d4c2178e4a519f114e07e385969639), `tests/test_registered_policy_atomic_disconnected_boundary_run935.py`, **4 new parametrized cases**. READ grants cannot become registered WRITE intents; a valid WRITE grant alone is denied without a one-shot; deriving a WRITE identity or persisting an intent/audit pair independently grants no dispatch; changing backend revision/effect changes bound action identity or rejects a READ-based claim. The backend is a never-execute sentinel, and all local authority flags remain false.
4. **Planner cross-process step-CAS and recovered RUNNING quarantine** — [`7d12eb02`](https://github.com/Iam-2squared/ark-ai/commit/7d12eb020cd8591b9be5f8712529174a5d3054f4), `tests/test_planner_cross_process_stale_step_wal_run935.py`, **2 new parametrized cases**. Two independent processes race from a common retained synthetic journal prefix. Duplicate same-step RUNNING can have only one winner; disjoint steps may both advance. Cold recovered RUNNING remains ambiguous, and no automatic replay or backend dispatch is authorized.

**8 NEW parametrized cases AUTHORED, 6 old cases repaired; these are not latest-head GREEN claims.** No production ARK source, frozen contract, protected evaluation, frontend/UI, Candidate, PR #5/#9 or main was changed. No local full repository pytest or target-PC runtime claimed.

## CI lineage / exact-SHA evidence

- Prior Run934 final checkpoint `5e13743b7e64101f59683a2b94bdc36d05e5802e`: [CI #44013582148](https://github.com/Iam-2squared/ark-ai/actions/runs/44013582148) **COMPLETED 6/6 GREEN** — Windows/Ubuntu × Python 3.11, 3.12 and 3.13; all six jobs inspected during this invocation. This does **not** validate Run935 changes.
- Context fixture repair `3f846a72`: [CI #44019456968](https://github.com/Iam-2squared/ark-ai/actions/runs/44019456968) **IN PROGRESS** at last inspection.
- Memory WAL `322a273c`: [CI #44019571242](https://github.com/Iam-2squared/ark-ai/actions/runs/44019571242) **IN PROGRESS**.
- Registry/policy/atomic `f24e8eba`: [CI #44019680263](https://github.com/Iam-2squared/ark-ai/actions/runs/44019680263) **IN PROGRESS**.
- Planner cross-process `7d12eb02`: [CI #44019752023](https://github.com/Iam-2squared/ark-ai/actions/runs/44019752023) **IN PROGRESS / QUEUED** (some jobs started).
- This documentation commit and later checkpoint each create independent automatic CI SHAs. At report creation, **latest Run935 six-job GREEN is not verified**. No duplicate manually triggered workflows.

## Audited frozen/free-only authority boundaries

V1/V2/Local UI/Launcher evidence, V3 frozen Contract #1/provenance/contamination/identity/reproducibility and protected V2 final evaluation are unchanged. [V3 pre-paid gate](https://github.com/Iam-2squared/ark-ai/blob/research/v3-learning-evaluation/docs/v3/PRE_PAID_COMPUTE_GATE.md) still requires immutable model/bytes, human-approved dataset and decisions, runtime/tool pins, hardware and explicit cost/timeout approvals before any external compute; **no** such work was initiated. PR #5 remains protected Draft/unmerged, PR #9 remains paused Draft/unmerged, PR #8 remains Draft/unmerged, main unchanged.

These fixtures do **not** prove authenticated human consent, trusted clock, immutable filesystem custody, cross-store atomic commit, physical-PC readiness or exactly-once external effects. A CAS winner/intent receipt is not proof that a real WRITE took place. No paid/cloud GPU/API, secrets, new accounts, model weights, irreversible data operation, notification, real backend action, main merge, Candidate promotion or protected evaluation opening.

## Next plan / 今後の方針

1. Confirm latest exact-head six-job CI, investigate any FAIL by logs, and fix minimally without weakening the guard or bypassing the ordinary GitHub write path. Particular focus: subprocess and SQLite WAL/SHM behavior on Windows.
2. After exact-head GREEN, scrutinize Memory cross-process WAL/SHM last-close and path alias cases; preserve existing strict sidecar refusal and coherent row/event/CAS generations. Recheck stale token and expiry/ABA under restart.
3. Extend Planner uncertain COMMIT-UNKNOWN manual-only quarantine and bounded recovery, then independently verify ToolRegistry/PermissionGate/durable occurrence/audit-before-action disconnected integration without dispatching anything real.
4. Maintain privacy-safe Personal Context/proactive/Observation backend fixtures and free V3 path/identity guards. Keep paid/training/credential/physical/protected/frozen/merge lanes blocked unless separately and explicitly approved.

**Overall ARK/JARVIS: NOT_PASSED.**
