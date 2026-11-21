# JARVIS Run564 — disconnected observation/transcript binding and restart denial custody

**Scope:** two reversible, free-only local-fixture source/test packages on Draft PR #8. No main merge or changes to frozen V1/V2/Local UI/Launcher, Memory, Planner or V3 contracts. This note is implementation evidence, **not** a JARVIS/PASS or device capability declaration.

## 1. Image/audio/transcript metadata bridge

New `src/ark/offline_observation_transcript.py` consumes explicit in-memory PNG and WAV fixture requests and a bounded tuple of synthetic transcript segment claims. It reuses the independently validated PNG/WAV metadata-pair inspector and the bounded frame-indexed transcript checksum validator. Inputs must carry exact `OfflinePngRequest`, `OfflineWaveRequest` and `TranscriptSegmentClaim` types; all five retained lowercase SHA-256 claims must be exact. The audit rechecks the original result-denial descriptors, native child validator callables, and input field carriers across two independent reinspection passes. It rejects changed metadata, incompatible owner/privacy/audio source, mismatch of the **retained transcript binding fingerprint**, forged permission descriptors, or mutation during callbacks.

The result is only `pair_sha256`, `transcript_fingerprint`, segment count, frame bounds, and a domain-separated envelope SHA-256. No transcript text, image pixels, PCM samples, command text or sensor I/O are emitted. A transcript checksum matching fixture bytes does **not** prove a speech recognizer produced that text. A caller-provided retained fingerprint does not prove independent historical storage or writer identity. The image and audio may be unrelated; no real-time synchronization, speaker identification or provenance is inferred.

New tests `tests/test_offline_observation_transcript_run564.py` exercise deterministic metadata-only output, stale or foreign owner/privacy/source/fingerprint, invalid input/text/audio, preinstalled and callback denial substitution, and mid-inspection mutation. Source and test commits received a targeted fixture escape correction so regular-expression end anchoring and binary PNG/WAV literals use the intended Python escapes. Counts are authored pytest parameter cases, not independent local pytest PASS observations.

## 2. Scheduler restart original-denial custody

`src/ark/offline_schedule_resume_review.py` now captures `OfflineScheduleResumeReview`'s five denial-only property descriptors at module import. The first `stable()` check rejects a preinstalled substitute that merely returns `False`, **before** the read-only SQLite witness scan or preview callback. The same original descriptors are rechecked across the three prior quarantine witness reads and final review. It still cannot trust caller time, advance the schedule, send notifications, dispatch tools or replay actions.

New `tests/test_offline_schedule_resume_denial_custody_run564.py` covers five preinstalled false-only replacements, one reentrant replacement through `ledger.inspect`, and a normal passive no-authority preview. The test fixture is a temporary SQLite database; no live timer or user event is created.

## 3. Exact-head CI and remaining gates

The preceding PR #8 checkpoint head `24f084443a81573e8dca6ad6fc19ee6fc04a1c20` passed all six CI matrix jobs (run [41513563714](https://github.com/Iam-2squared/ark-ai/actions/runs/41513563714)). For the new commits, only an exact-head completed six-job run may establish GREEN; source/test code and this note are not a substitute for CI. Any failing run must be diagnosed from its own logs, corrected through the ordinary GitHub Contents API, and revalidated. The canonical `docs/PROJECT_STATUS.md` is updated once at the end after re-reading actual heads.

**Remaining explicit boundaries:** real microphones/cameras, acoustic ASR, authentic owner/consent/clock, retention policy, cross-device timing, guaranteed exactly-once ToolBackend actions, irreversible effects, protected V2 final evaluation, Candidate generation/promotion, external GPU and paid services are **not authorized or proven**. PR #5 remains Draft, unmerged; ARK/JARVIS/V3 remain **NOT_PASSED**.
