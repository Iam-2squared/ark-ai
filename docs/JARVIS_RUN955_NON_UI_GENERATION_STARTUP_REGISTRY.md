# ARK AI Run955 — Non-UI event hydration, restart witness carrier, registry bind CI triage

**Work basis:** `c01532f51d87e4f95b530a93cbe1473a0cc95ab7` (Run954 checkpoint, Draft PR #8).  
**Latest source/test HEAD before this report:** `c92988cbbfac15d5714310437ecc0e0bee2753a4`.  
**Branch:** `research/jarvis-foundations`. **Scope:** synthetic disconnected, no UI, zero new paid services.  
**Overall ARK/JARVIS:** NOT_PASSED. **No exact-head CI GREEN claim before completion.**

## Package A — opt-in Memory generation-CAS SQLite event prehydration

- Source commit [4228c892](https://github.com/Iam-2squared/ark-ai/commit/4228c8929c7dad2c6c3f319ceaa51fa61b6d51b0) changes only `src/ark/memory/generation_fenced_cas.py`.
- A pinned SQLite transaction now rejects owner/namespace TEXT whose byte length exceeds the frozen Memory v1 1,024-byte storage bound, non-TEXT identities, malformed operation byte widths and noninteger event revision/timestamp **before materializing scoped event rows in Python**.
- Test commit [dad76b80](https://github.com/Iam-2squared/ark-ai/commit/dad76b80f2acc04f0038793bd3fd7b45c433cfa1): 4 parametrized disposable-SQLite corruption cases. Both observation and generation-fenced update must reject; memory row and event count remain untouched. No frozen Memory v1 schema/API changes or local permission grant.
- This is an admission bound, **not** authenticated event provenance, historical custody, prevention of in-memory process compromise or a trusted writer identity.

## Package B — disconnected startup retained witness carrier

- Source commit [1c9387f3](https://github.com/Iam-2squared/ark-ai/commit/1c9387f34566a377422b8b96088421cdeded7164) pins the three distinct retained-witness dataclass slot and lookup descriptors at import time and verifies their identity **before reading** caller-retained cross-store tips.
- Test commit [8cb3d605](https://github.com/Iam-2squared/ark-ai/commit/8cb3d60553e5173cde943486add9a1897f81ad68): 6 parametrized slot/lookup substitution cases across Memory, Personal Context replay and Proactive due reservations, followed by a clean read-only verification.
- No cross-store atomicity, trusted clock, startup permission, personal-context release, automatic replay or real dispatch is conferred.

## Package C — exact Run954 CI failure triage and minimal production correction

- Run954 checkpoint CI [#44204595192](https://github.com/Iam-2squared/ark-ai/actions/runs/44204595192) reported 5/6 failed jobs at the sampled time. Ubuntu Python 3.11: **17,326 passed, 1 skipped, 1 failed**, failing `test_registry_scope_admission_run954.py::...surrogate_scope...[bind]`.
- Root cause: `ToolRegistry.bind()` reconstructed a frozen `ToolCall` *before* applying `resolve()`'s existing strict UTF-8 scope validation. The request-ID serializer therefore raised raw `UnicodeEncodeError`, contrary to the opt-in fail-closed `ValueError` contract. Backend was not executed.
- Narrow source fix [c92988cb](https://github.com/Iam-2squared/ark-ai/commit/c92988cbbfac15d5714310437ecc0e0bee2753a4) puts NUL/surrogate admission before `ToolCall(*original)` in `bind()`, matching `resolve()` and preserving frozen ToolCall v1, registration, backend, and permission semantics.
- Existing Run954 parametrized tests verify both `resolve` and `bind`; no weakened assertions, ignored failures, or duplicate workflow launch.

## CI and exact-head limits

- Run954 previous checkpoint [#44204595192](https://github.com/Iam-2squared/ark-ai/actions/runs/44204595192): **known FAILED** at this report preflight, even though one Windows job was still running when sampled.
- [#44210140012](https://github.com/Iam-2squared/ark-ai/actions/runs/44210140012) Memory source; [#44210343825](https://github.com/Iam-2squared/ark-ai/actions/runs/44210343825) startup source; [#44210441300](https://github.com/Iam-2squared/ark-ai/actions/runs/44210441300) Memory tests: **IN PROGRESS** when sampled.
- [#44210505325](https://github.com/Iam-2squared/ark-ai/actions/runs/44210505325) startup tests; [#44210721776](https://github.com/Iam-2squared/ark-ai/actions/runs/44210721776) registry repair: **QUEUED** when sampled. Intermediate heads may inherit Run954 registry failure; assess their exact commit identities.
- **Ten tests authored**, not yet six-matrix GREEN. No local full pytest or physical Windows/GGUF validation. CI must independently establish Linux/Windows, Python 3.11–3.13 compatibility.

## Boundaries and next actions

- PR #5 (V3), PR #8 (non-UI foundations), PR #9 (paused Next Generation UI) all remain Draft/unmerged; main unchanged. Frozen V1/V2/Local UI/Launcher/Observation-v1/V3 contracts/evidence untouched. No real tool backend, camera, microphone, screen capture, notification, paid service or external GPU, Candidate adapter/weights/training, protected evaluation, credential/account connection, irreversible action or main merge.
- Next: (1) confirm exact repaired HEAD CI 6/6 and fix any concrete failure via normal writes; (2) separately audit generation-CAS **row** hydration before `SELECT *` and WAL/SHM lifecycle, without modifying a path while its CI is validating; (3) integrate Planner/registry/permission/atomic audit only after lower-layer exact-head GREEN; (4) continue Personal Context privacy and Proactive durable occurrence safeguards in isolated non-UI workstreams.
