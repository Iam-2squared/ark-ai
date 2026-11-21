# ARK AI Run957 — disconnected proactive source bytes, Memory scalar admission, privacy veto clocks

## Scope and work basis

- **Work-basis HEAD:** `3422bd6335a34c9b2689f31c993d6b1d5d48732b` on Draft PR #8 (`research/jarvis-foundations`).
- **Latest source/test HEAD at this report:** `216f55a94d542e6cd6a071ce0745921e65c9bbfb`.
- **State:** ARK/JARVIS **NOT_PASSED**. This report covers opt-in, disconnected, zero-new-cost, non-UI diagnostics and tests. It does not authorize real capture, notification, ToolBackend execution, model training, hardware, paid API/GPU or main merge.
- Frozen V1/V2/Local UI/Launcher/Observation-v1, V3 Contract #1 and protected evaluation/evidence gates are unchanged. PR #5 and paused UI PR #9 remain untouched, Draft and unmerged.

## Packages and exact commits

1. **Proactive Observation source digest ingress:** [`699761e0`](https://github.com/Iam-2squared/ark-ai/commit/699761e0b6611b34b480824bafdf1b0d88a573d6) makes the independently callable synthetic observation-source digest reject **over 1024 UTF-8 encoded bytes** before the local hash, matching the already-frozen ObservationEnvelope byte ceiling. Its prior 1024-codepoint check admitted multibyte labels that no valid envelope can carry. This changes only the optional proactive local binding guard, not Observation-v1 or real sensor access. [`f0be32f0`](https://github.com/Iam-2squared/ark-ai/commit/f0be32f018c5c1be99776545f00056edc8e03e14) adds **14 parametrized tests**: ASCII/two-byte/four-byte exact boundaries, over-budget private source rejection before hashing, invalid Unicode, and non-text/blank rejection.
2. **Memory mutation scalar prehydration:** [`8044bd72`](https://github.com/Iam-2squared/ark-ai/commit/8044bd7278b1d6cba5996021b15fd99dd5510a7a) adds **7 parametrized tests** of malformed persisted owner/namespace/source (BLOB), expiry (BLOB), revision (BLOB), short digest and a valid cold Unicode-free revision/expiry update/delete path. Both put/delete reject malformed primary-key targets; original row and event history must remain unchanged. **Initial [CI #44224339148](https://github.com/Iam-2squared/ark-ai/actions/runs/44224339148) FAILED 6/6 in Ruff F841** for one unused healthy fixture variable. [`d0902626`](https://github.com/Iam-2squared/ark-ai/commit/d09026265937502cf7696fbe8561f80a5da2ae9a) retains the variable and asserts initial revision/expiry; no safety assertion removed.
3. **Privacy revocation clock partition:** [`216f55a9`](https://github.com/Iam-2squared/ark-ai/commit/216f55a94d542e6cd6a071ce0745921e65c9bbfb) adds **7 tests** of invalid exact timestamp classes/ranges, unrelated scope rollback denial, cold restart of a persisted veto, accepted equal-time independent vetoes, and unchanged digest-only rows. Veto absence is not consent; no real deletion/regrant or cross-store atomicity is claimed.

**28 authored parametrized cases** across three independent packages, with one corrected test lint error. No full local pytest was available. Do not report the 28 tests as six-platform GREEN without exact-head CI.

## CI and evidence context

- [Run956 source/test repair CI #44221983516](https://github.com/Iam-2squared/ark-ai/actions/runs/44221983516) at work-basis `3422bd6335a34c9b2689f31c993d6b1d5d48732b`: COMPLETED/GREEN all 6 matrix jobs (observed after starting this run). Earlier Run956 CI failures were on preceding HEADs and cannot be borrowed as evidence.
- New proactive source [CI #44224107127](https://github.com/Iam-2squared/ark-ai/actions/runs/44224107127) and test [CI #44224182697](https://github.com/Iam-2squared/ark-ai/actions/runs/44224182697): started, outcomes must be verified separately.
- Initial Memory tests [CI #44224339148](https://github.com/Iam-2squared/ark-ai/actions/runs/44224339148): FAIL due to F841, repaired at a later exact SHA. Repair [CI #44224523215](https://github.com/Iam-2squared/ark-ai/actions/runs/44224523215): running at report construction.
- Privacy [CI #44224652273](https://github.com/Iam-2squared/ark-ai/actions/runs/44224652273): running at report construction. Its HEAD is the latest source/test basis before this report and checkpoint.
- Report/checkpoint documentation commits may each trigger CI. There was no manual duplicate workflow launch.

## Free-only limitations and next plan

1. Check the repaired exact-source/test CI six-job matrix; on failures, inspect job logs and use only the normal contents API update path to make the narrowest semantics-preserving repair.
2. Continue Memory same-transaction storage-class ingress and WAL/SHM/ABA/expiry coherent snapshots; no writer custody, authenticated event provenance or cross-store atomicity implied by local SQLite digests.
3. Continue Planner RUNNING/COMMIT-UNKNOWN quarantine, immutable ToolRegistry and exact PermissionGate, persistent one-shot occurrence and audit-before-action, disconnected mock-only executor, without replaying ambiguous WRITE.
4. Continue privacy-safe Context history/revocation, Proactive cold state, Observation non-capture fixtures, V3 path/approval/reproducibility guards with no external GPU/paid compute. Real PC gate, protected final evaluation, Candidate creation/promotion, credential linkage, live tools and main merge remain blocked pending the exact required authorization.

**No UI/frontend changes. ARK/JARVIS NOT_PASSED.**
