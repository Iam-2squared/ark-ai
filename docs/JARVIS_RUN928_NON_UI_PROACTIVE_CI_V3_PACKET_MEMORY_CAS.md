# ARK AI Run928 — non-UI proactive CI compatibility, detached V3 identity, Memory CAS restart

**Work-basis HEAD:** `42906296ba8702c09715a2990b790e56987ec468` (Run927 checkpoint). **Complete source/test HEAD at this report write:** `febf802cd0342f4c40f4dc4f9c70a5bbc184bd33`. **Branch:** `research/jarvis-foundations`, Draft PR #8. This document is non-normative technical evidence; V1/V2/Local UI/Launcher freezes, Observation v1, protected evaluation, PR #5 and paused PR #9 are unchanged.

## A. Real CI regression and safety-preserving correction

The prior Run927 six-job run [#43960492431](https://github.com/Iam-2squared/ark-ai/actions/runs/43960492431) produced **Ubuntu 3.11/3.12/3.13 FAIL**, with four failures (3 parametrized + 1) in earlier synthetic proactive freshness tests. Ubuntu 3.11 job `133626270075` reported `4 failed, 16742 passed, 1 skipped`; Windows job completion was not verified at the inspection snapshot. The three `test_reflected_mid_review_evidence_drift_is_denied` cases and one phased continuity callback test had required late injected `SyntheticTriggerPolicy.identity` callbacks plus an error matching `evidence changed`.

Run927's stronger source pregetter correctly rejects a replaced class-level policy identity method **before executing its callback** with `SyntheticTriggerRejected("synthetic trigger policy contract changed")`. Restoring late callback execution would weaken the new security boundary. Consequently two **test-only** normal Contents commits adapt four earlier assertions to early fail-closed rejection, zero injected callbacks, and no reflected receipt/path/witness mutation:

- [`7ef777e8`](https://github.com/Iam-2squared/ark-ai/commit/7ef777e87b3ab1c6a38c3774370b9d0cbd4b23bf): 3 parametrized freshness cases revised, preserved current source.
- [`c932bf63`](https://github.com/Iam-2squared/ark-ai/commit/c932bf637d4882886dea0a03554194c84c20008b): phased continuity case revised; unmodified transient-epoch assertions continue to exercise independent callback drift.

**No production proactive source, policy schema, timers, notification or dispatch capability changed in this repair.** These commits are authored fixes, not an exact-head CI PASS claim.

## B. Independent free-only V3 packet fidelity (8 NEW synthetic tests)

[`08805aa8`](https://github.com/Iam-2squared/ark-ai/commit/08805aa8b27880b6da8763254ba252f9a40fbf6b) created `tests/test_v3_detached_packet_identity_run928.py`. Seven table-driven cases independently alter valid synthetic device/capacity/tokenizer/timeout/VRAM/wall-time evidence and require both actual canonical packet-byte SHA-256 and normalized crossbind digest to change. One case distinguishes numerically equivalent `12` and `12.0`: exact packet byte digest must change, normalized semantic crossbind digest remains equal. All reviews explicitly retain **FALSE** for paid compute, training, Candidate promotion and independent provenance. This is detached in-memory parser testing: **no GPU, paid provider, real Candidate, physical PC, protected final evaluation, approval or promotion**.

## C. Independent Memory identity, stale CAS and cold reopen (3 NEW synthetic tests)

[`febf802c`](https://github.com/Iam-2squared/ark-ai/commit/febf802cd0342f4c40f4dc4f9c70a5bbc184bd33) created `tests/test_memory_multiscope_cas_reopen_run928.py`. Two scope parametrizations use the same source ID but distinct owner/namespace to assert different deterministic Memory IDs, cross-scope `get`/wrong-scope `delete` denial, cold-reopened private contents and separate create event histories. A third test has two independent SQLiteMemoryStore instances, one committed revision-2 update, stale revision-1 update/delete conflict, and reopened data plus exactly the create/update audit events. Only disposable pytest temporary database paths, no real user memory, export or deletion.

## CI, evidence, and limitations (snapshot from real GitHub APIs)

- Last prior fully observed six-job GREEN before the proactive source regression: [#43958824248](https://github.com/Iam-2squared/ark-ai/actions/runs/43958824248), exact preceding Atomic SHA `7f8bde499ec6726162155c5ce9d5c0ba0aee9da7`. Run927 source+test [#43959425252](https://github.com/Iam-2squared/ark-ai/actions/runs/43959425252) and source [#43959294740](https://github.com/Iam-2squared/ark-ai/actions/runs/43959294740) **FAIL**.
- First proactive repair [#43963475823](https://github.com/Iam-2squared/ark-ai/actions/runs/43963475823) **IN PROGRESS** at snapshot; second repair [#43963537128](https://github.com/Iam-2squared/ark-ai/actions/runs/43963537128) **IN PROGRESS**.
- Detached V3 package [#43963682796](https://github.com/Iam-2squared/ark-ai/actions/runs/43963682796) **QUEUED**; Memory package [#43964014776](https://github.com/Iam-2squared/ark-ai/actions/runs/43964014776) **QUEUED**.
- **11 new synthetic test cases authored; 4 existing parametrized assertion cases corrected. These are NOT confirmed passes.** Local full pytest, GGUF validation, physical PC integration, trust/consent or external-effect exactly-once are not proven. No duplicated manual CI workflow requested.

## Frozen boundaries and next dependent work

Keep PR #5 protected, PR #8 foundations Draft/unmerged, PR #9 UI paused Draft/unmerged; no main merge, UI/frontend work, protected V2 evaluation, real Candidate/adapter/weight generation or promotion, paid compute/API, new credential, external real tool, privacy export, forced Git write or independent authority fabrication. **ARK/JARVIS NOT_PASSED.**

Priorities: (1) inspect exact repaired source/test six-job CI and repair only real errors while continuing unrelated code lanes; (2) keep WAL/SHM held-file/alias race and Memory coherent CAS/expiry/event investigation disposable and deny-only; (3) verify Planner COMMIT-UNKNOWN retained manual review before registry-bound PermissionGate → durable occurrence/authorization → independently trusted audit-before-action → disconnected mock integration; (4) continue privacy-safe Personal Context, proactive/Observation backends and V3 free-only guards. No automatic ambiguous WRITE replay.
