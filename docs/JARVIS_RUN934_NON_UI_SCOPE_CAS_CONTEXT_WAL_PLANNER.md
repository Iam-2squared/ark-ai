# ARK AI Run934 — scoped Memory CAS, Personal Context detached evidence, WAL audit, Planner branch recovery

**Recorded:** 2026-11-17T12:54:38.268+09:00 (JST reporting time only; not a trusted audit or permission clock).  
**Basis:** `ad5e4b0fdede3aeefab5bf6970ea2caea9d7928b` / Draft PR #8 / `research/jarvis-foundations`.  
**Source/test work HEAD:** `f7f3eb20a99f10dddfa0887ffaedc24503a37a10` (re-read from live PR and branch immediately before this report).  
**Overall:** NOT_PASSED. Free-only, synthetic/disconnected non-UI foundation tests. No frozen-contract change or real dispatch.

## Four independent test packages (17 parametrized cases authored)

1. **Memory scoped CAS under unrelated corrupt data** — [`cba2a684`](https://github.com/Iam-2squared/ark-ai/commit/cba2a6843629788a659e3fab00e98c1663611b48), `tests/test_memory_foreign_blob_cas_write_run934.py`, **6 cases**. A BLOB-affinity corrupt content/metadata/source_id row in another namespace or owner is never repaired/read by a normal local CAS update. After a legitimate two-revision local write, stale revision 1 is refused, local events remain create/update, global event count 3, foreign BLOB stays unchanged. Only disposable fixture SQLite databases.
2. **Personal Context detached receipt rebinding** — [`494cd302`](https://github.com/Iam-2squared/ark-ai/commit/494cd302d8208a98cfc8de7bfb2a87afc32fb913), `tests/test_personal_context_rehashed_detached_binding_run934.py`, **6 cases authored; coverage limitation below**. Synthetic owner, scope, record id, content, extra field, empty batch changes are challenged with a recomputed detached digest; no live user context or export.
3. **Atomic pre-action WAL snapshot isolation** — [`6e091b56`](https://github.com/Iam-2squared/ark-ai/commit/6e091b564ad189fd8b7cba7e4d34b0fa9c9862dd), `tests/test_atomic_preaction_wal_reader_cas_run934.py`, **2 cases**. In a disposable SQLite WAL database, old read-only/read-write reader transactions retain a coherent pair of one intent/one audit when another handle atomically commits two rows; a fresh handle must reject stale retained CAS and observe both new rows. The returned witness grants no external action authority.
4. **Planner branch-prefix CAS and terminal fan-in** — [`f7f3eb20`](https://github.com/Iam-2squared/ark-ai/commit/f7f3eb20a99f10dddfa0887ffaedc24503a37a10), `tests/test_planner_shared_prefix_disjoint_terminal_run934.py`, **3 cases**. Two independent handles can progress distinct branches against a valid earlier retained prefix; a duplicate stale same-step revision cannot pass. Cold recovery projects SUCCEEDED/FAILED/CANCELLED and refuses dependency join after failure. No backend callback invoked.

**Test quality issue discovered during source re-read (must be corrected on a subsequent permitted test write after the current CI lane finishes):** The Personal Context test's private `_DOMAIN` constant is encoded with a *literal backslash plus zero* (`\\0`) rather than the protocol's NUL delimiter. This means the six assertions can reject the altered packet at its digest preflight, *not* necessarily at fixture-semantic binding. Their current apparent PASS **must not be called proof of validly rehashed detached receipt rejection**. Correct with `b"ARK-local-context-fixture-preview-v1" + bytes((0,))`, assert the matching protocol domain, and run exact-HEAD CI. No production safety guard was weakened. This is a test fixture defect, not an observed live security bypass.

## GitHub CI / exact-head evidence

- Prior fully verified [Run933 checkpoint CI #44005982177](https://github.com/Iam-2squared/ark-ai/actions/runs/44005982177), SHA `ad5e4b0f...`: **6/6 GREEN**, Windows and Ubuntu × Python 3.11, 3.12 and 3.13, all six individual jobs inspected at Run934 start.
- [CI #44012859174](https://github.com/Iam-2squared/ark-ai/actions/runs/44012859174), SHA `f7f3eb20a99f10dddfa0887ffaedc24503a37a10`: **IN_PROGRESS** at read.
- [CI #44012735089](https://github.com/Iam-2squared/ark-ai/actions/runs/44012735089), SHA `6e091b564ad189fd8b7cba7e4d34b0fa9c9862dd`: **IN_PROGRESS** at read.
- [CI #44012656090](https://github.com/Iam-2squared/ark-ai/actions/runs/44012656090), SHA `494cd302d8208a98cfc8de7bfb2a87afc32fb913`: **IN_PROGRESS** at read.
- [CI #44012593519](https://github.com/Iam-2squared/ark-ai/actions/runs/44012593519), SHA `cba2a6843629788a659e3fab00e98c1663611b48`: **IN_PROGRESS** at read.
- The report/checkpoint themselves create later automatic CI at different SHAs. Their new run IDs and six-job outcomes cannot be known before their commits. **Latest test HEAD all-six GREEN NOT VERIFIED**, and 17 authored cases are not represented as 17 successful cross-platform checks.

## Frozen and free-only gates

Draft PR #5 remains protected and unmerged; UI Draft PR #9 is paused, untouched and unmerged. Frozen V1/V2/Local UI/Launcher evidence and protected evaluation boundaries are not altered. No real model/Candidate, GPU, chargeable APIs/services, paid compute, secrets, accounts, physical PC, real tool backend, notification, destructive action, main merge or human-approval claim. A local SQLite WAL snapshot, registry binding or SHA-256 digest is neither independent provenance nor trusted-time audit, human consent, external exactly-once guarantee, or cross-store atomicity.

## Next plan / 今後の方針

1. Resolve full six-job exact-head CI for all four packages; if FAILED, inspect job-level logs and fix the smallest semantics-preserving issue. Specifically correct the detached-preview NUL-domain test fixture once its in-flight lane has completed.
2. Further reproduce the independent-owner Memory WAL/SHM process race with disposable fixtures, preserving strict alias/sidecar refusal and no silent data repair.
3. Improve Memory coherent row/event CAS/ABA and Planner COMMIT-UNKNOWN manual quarantine, then integrate registry-bound PermissionGate, durable occurrence and audit-before-action in disconnected mode only after exact-head GREEN.
4. Continue privacy-safe Personal Context lifecycle, proactive scheduler and observation back-end fixtures; keep V3 free-only approval/path/identity/reproducibility checks separated from protected V2 evaluation and paid GPU actions.

**ARK/JARVIS overall NOT_PASSED.**
