# ARK AI — Run729: private PCM/WAV codec preaccess and V3 free-only review

**Recorded (administrative JST):** 2026-11-09T13:49:00.044+09:00. This is not a trusted action clock.
**Branch/PR:** `research/jarvis-foundations`, [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8), OPEN/UNMERGED.
**Initial work-basis HEAD:** `f5acc1dd895b0bf6b2fed249ef70292328e4ebda` (Run728 checkpoint).
**Last confirmed source/test HEAD before this report:** `d6bd337a61e53f0c682f5cd7c79d0eb4b2ffd3da`.
**Scope:** Free-only, offline/mock, backend only. No UI work, new accounts/secrets, paid/external compute, model/GPU execution, real tools/sensors, destructive repair, training, V2 opening, Candidate, promotion or main merge.

## Package A — CI diagnosis and earlier fail-closed PCM output factory refusal

[Run728 exact checkpoint CI #42559843245](https://github.com/Iam-2squared/ark-ai/actions/runs/42559843245) **6/6 FAILED**. Actual Ubuntu Python 3.11 log: **11,481 PASS, 8 FAIL, 1 SKIP**. The eight failures were confined to `tests/test_offline_pcm_result_custody_run499.py`: seven malicious result factories and one substituted result class expected the previous late-stage `fields changed` / `type changed` rejection. The now-pinned resampler import-original `ResampledPcm` refuses before the attacker-controlled factory executes, with `PCM dependency or carrier authority changed`.

[Normal Contents API fix `04978c7`](https://github.com/Iam-2squared/ark-ai/commit/04978c79c88c5fd1ba0abf0b5e04a75849334b5b) requires the forged callback to execute **zero** times and matches the earlier failure. Production resampler safety was **not** weakened. These fixed tests must still pass on exact new HEAD and all six OS/Python combinations.

## Package B — offline PCM activity-region codec/digest preaccess

[Source `15ea08d`](https://github.com/Iam-2squared/ark-ai/commit/15ea08d633315aa4cf9c5f903caa2397088b41de) adds import-original references to `hashlib`, `struct`, SHA-256, `iter_unpack`, rate policy, digest pattern and byte budget. Guards execute **before** raw bytes are hashed or decoded, and before detached comparison touches a report. Rechecks bracket frame reads and returned metadata. This remains simple deterministic fixture activity, not VAD, ASR, sensor authentication or independent permission evidence.

[New tests `a44c541`](https://github.com/Iam-2squared/ark-ai/commit/a44c541ca6144325e46669d30fc776f7942833cb): **15 authored parameter-expanded cases** (7 hostile dependency surfaces × detect/verify, plus one valid control). Poisoned SHA/codec callbacks must have **zero invocations**; benign metadata remains detached and non-authorizing.

## Package C — strict in-memory WAV codec/digest preaccess

[Source `b42db44`](https://github.com/Iam-2squared/ark-ai/commit/b42db440a7976be528f70b1e9afff798a1300d88) pins the original SHA-256, `struct.unpack_from`, module bindings, checksum regex and WAV size/duration caps in the existing request/receipt authority guard. It refuses substitution before reading caller-private WAV bytes, and rechecks at existing parsing/receipt checkpoints. No capture, ASR, disclosure or file I/O added.

[New tests `d1ffa63`](https://github.com/Iam-2squared/ark-ai/commit/d1ffa634998b3c20da521ae83f1038cbba749d0e) (fixture corrected by [`8d55d9f`](https://github.com/Iam-2squared/ark-ai/commit/8d55d9f4340960f97ec0d4d3e4d7034f7930ecaf)): **8 authored cases** (seven substitutions plus canonical 80-frame non-authorizing control). [Inherited WAV constructor injection test `d6bd337`](https://github.com/Iam-2squared/ark-ai/commit/d6bd337a61e53f0c682f5cd7c79d0eb4b2ffd3da) now distinguishes an existing forged constructor denial from a *pre-entry* digest-module swap denial. The forged constructor must never run.

**Total new cases:** 23 authored parameterized tests. Full multi-OS passing evidence is **not yet available**. A source/CI run being queued or in progress is **not** equivalent to a completed PASS.

## Package D — independent free-only V3 review; PR #5 untouched

Exact read of [Draft PR #5 at `805b377`](https://github.com/Iam-2squared/ark-ai/pull/5) established that the earlier documented preflight measurement cross-binding issues now have checks in `src/ark/learning/preflight.py`: device, measured VRAM tolerance, tokenizer probe, allocated-versus-reserved-versus-measured VRAM, and finite bounded wall time. The [existing review](V3_FREE_GUARD_REVIEW.md) describes earlier state; **do not reclassify those findings as outstanding without checking current source**.

`src/ark/learning/export_plan.py` now resolves the output parent, refuses symlinked parents, forbids output overlap with base/Candidate source roots and prevents generated output matching the deployed Current model. It is **plan construction**, explicitly not handle-stable TOCTOU custody: further proof of all input/output canonical disjointness, alias handling and a stable read-only execution context is still required before any actual export.

The earlier [pre-compute runtime gap review](V3_PRECOMPUTE_RUNTIME_GAPS_20260929.md) separately documents one-shot attempt consumption, separate runtime-consumed approval artifacts and verify-to-use identity concerns; this run neither closes those claims nor opens a protected gate. No real Candidate adapter/weight generation, GPU/preflight or paid provider was attempted. PR #5 remains Draft/unmerged.

## Exact CI and safety caveats

- **Completed failure evidence:** #42559843245 = 6/6 FAIL at exact initial HEAD. Ubuntu 3.11 11,481 PASS / 8 FAIL / 1 SKIP.
- **Most recent tested source/test commit at authoring:** `d6bd337a61e53f0c682f5cd7c79d0eb4b2ffd3da`. [CI #42563564710](https://github.com/Iam-2squared/ark-ai/actions/runs/42563564710) was QUEUED at read, not verified GREEN. Subsequent documentation/status commits have separate HEADs and CI.
- Built-in module identity comparisons provide local fail-closed consistency and callback preaccess, **not** a hostile interpreter sandbox, signed provenance, consent, trusted clock, true exactly-once effect, or permission to execute tools.
- V1/V2/Local UI/Launcher frozen contracts/evidence unchanged; protected V2 evaluation unopened. Draft PR #9 UI paused/unmodified; PR #5 draft/unmerged; no main merge.
- **Overall ARK/JARVIS/V3: NOT_PASSED.** Prioritize checking exact latest CI (especially Windows), fixing actual regressions narrowly, then Memory CAS/COMMIT-UNKNOWN, Planner retained READ evidence and registry-bound durable audit/mock integration.
