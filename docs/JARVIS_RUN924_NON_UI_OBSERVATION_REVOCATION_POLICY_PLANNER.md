# ARK AI Run924 — Observation, revocation, registered policy and Planner admissions

**Observed at JST:** 2026-11-17T03:55:56.305+09:00 (reporting wall-clock observation only; NOT an authenticated clock for tool actions).
**Basis:** `9813f0c97943efae130d5fa6911e3bb5151e59f6` / Draft PR #8 `research/jarvis-foundations`. **Complete source/test/fix HEAD before report:** `fb89472fedad186097d317a412c94d01efca5df9`. Existing protected PR #5 and paused UI PR #9 untouched; main not merged. **ARK/JARVIS NOT_PASSED.**

## Four independent free-only non-UI work packages — 27 regression cases authored

1. **Observation metadata admission**: source `d83de18262cb948e50fb5ec716fc3117a531e335`, test `d1705d0a308a6e991f3241685aa32230cedd4456`. The exact `ObservationEnvelope` constructor now rejects NUL in source, adapter or privacy label *before* its provenance digest. Tests cover six NUL-at-entry cases, three reflected post-init drifts and one healthy deterministic identity. This aligns the direct envelope path with the fixture adapter's prehash NUL fence. No camera, microphone, network or live data used.
2. **Personal Context revocation catalog prehydration**: source `74086366976ccdcf6cabaf5d55a6441b17f0b55c`, tests `f8c926d173bd6c61f587ec93897164cfa92383a7`. The revocation v1 SQLite checker now limits total BLOB-byte size for `sqlite_master` type+name+tbl_name (4,096 bytes), as well as the unchanged two-object and DDL-size checks, before hydrating full schema rows into Python. Six in-memory writable-schema corruption cases and one legitimate schema case. Frozen persisted DDL untouched. The local scope digest never establishes authenticated consent.
3. **Registered policy-to-backend non-dispatch proof**: test `4446d9fe716d460521798b6256a763cbad117f33`. Six cases combine immutable `ToolRegistry` bindings, exact-scope `PermissionGate`, denied/locally accepted READ and WRITE requests, replay rejection within one gate and deliberate non-inheritance of WRITE token state across gate instances. Every case uses a poison synthetic backend whose execution counter must remain zero. Importantly, local authorization is **not** persistent one-shot approval, trusted clock, authenticated audit or real execution authority.
4. **Planner journal topology preaccess**: source `39f394cad6dd1205710ba16314f2a7bb6dd9562b`, test `5bea03908b88450dabbe3dfa7268136569adc5d0`. Before the early membership generator can touch `step.step_id`, refuse a reflected non-tuple, over-4,096-element tuple or foreign step object. Three hostile carrier cases assert neither arbitrary getter/len nor SQLite open occurs; one healthy disposable synthetic RUNNING recovery remains ambiguous with no auto-retry or dispatch.

**Quality correction:** test-only Ruff import ordering `fb89472fedad186097d317a412c94d01efca5df9`, after intermediate CI failed. No public tool contract, external adapter, stored schema, frozen V1/V2/UI/Launcher, Candidate, protected V3 or main code changed.

## Independent WAL/SHM diagnostic note — not a runtime proof

A separately executed disposable Linux Python 3.13.5 / SQLite 3.46.1 two-process experiment (three observations each with/without a keeper connection) recorded normal `-shm` link-count transitions **only after all bootstrap SQLite connections were explicitly closed**. With no keeper, a held `-shm` FD became unlinked after child last-close; with keeper, it stayed linked after child close and became unlinked on keeper close. Cold count remained one. In a deliberate *leaked connection* control, using `with sqlite3.connect(path)` without `closing(...)` left the bootstrap handle alive and the sidecar still linked even though a separate cold read succeeded. Python's SQLite connection context manager handles transactions but does **not** close the connection. These are generic disposable local probes, **not the ARK real-process race or independent proof of its resolution**. Never treat an unlinked path or successful cold read as permission to auto-retry UNKNOWN or external WRITE.

## CI snapshot and boundaries

- Prior Run923 exact branch HEAD `9813f0c9`: [Actions #43923887824](https://github.com/Iam-2squared/ark-ai/actions/runs/43923887824) **GREEN**, six of six completed jobs (Ubuntu/Windows × Python 3.11–3.13).
- During this invocation several intermediate synthetic PR runs (#43932828645, #43932942950, #43933291695, #43933368182) failed the single import-order Ruff finding in `test_revocation_catalog_prehydration_run924.py`. Small test-only correction is committed at `fb89472f`.
- [Corrected source/test HEAD CI #43933660559](https://github.com/Iam-2squared/ark-ai/actions/runs/43933660559): **IN PROGRESS** at report observation; Ruff step **GREEN across all six job environments**. Full pytest on the corrected exact source HEAD not yet certified. Report and checkpoint commits create their own automatic workflows. No manual duplicate workflow run.
- No full local ARK test suite, target-PC GGUF, paid GPU/API, live credential, private user record, real tool dispatch, protected V2 final evaluation, Candidate training/promotion or main merge. PR #5/#8/#9 remain Draft and unmerged; UI remains paused.

## Next plan

1. Inspect exact newest HEAD full six-job pytest. On failure, analyze job logs, make only semantics-preserving fixes via normal GitHub Contents API.
2. Continue bounded disposable cross-process WAL/SHM held-handle/path race checks; confirm every bootstrap connection's close and independently retained evidence, do not allow UNKNOWN replay.
3. Strengthen Memory coherent event/CAS/expiry and Planner COMMIT-UNKNOWN retained-prefix crash recovery, keeping denial-only recovery.
4. Integrate pinned registry → exact gate → persistent reservation/occurrence → independently trusted clock audit-before-action → disconnected mock only when prerequisite exact-head GREEN evidence exists. No live WRITE.
5. Maintain UI pause and all free-only, no-merge, no-evaluation, no-Candidate and frozen-contract boundaries.
