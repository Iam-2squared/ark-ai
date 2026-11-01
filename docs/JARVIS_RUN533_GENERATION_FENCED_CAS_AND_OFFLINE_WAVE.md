# Run533 — Opt-in Memory generation-fenced CAS and disconnected WAV energy pipeline

**Scope:** free/local-first, isolated and reversible. PR #8 remains Draft and unmerged. Memory v1 public contracts/schema and V1/V2/Local UI/Launcher frozen evidence are NOT changed. No external ToolBackend, microphone, network, GPU, paid service, Candidate, protected evaluation or real-world write dispatch.

## Package A — Memory: transactional lifetime-fenced update

- `src/ark/memory/generation_fenced_cas.py`: opt-in `observe_memory_generation_for_cas` and `generation_fenced_memory_update`, without changing frozen `SQLiteMemoryStore.put/delete` semantics.
- A bounded (40,000-event maximum) coherent SQLite observation binds deterministic memory ID, current row image, complete event-prefix hash, current revision, last event ID and the current lifetime's **create event ID**.
- `generation_fenced_memory_update` starts `BEGIN IMMEDIATE`, validates exact v1 schema, full event lineage, row identity and all token fields **under the same write lock**, then conditionally updates the existing row and appends its corresponding `update` event in the same SQLite transaction. It refuses a missing row and does not create/recreate on its own.
- The token is **not cryptographically authenticated** and grants no consent or external action. Concurrent legitimate writers with the same retained token cannot both update the same lifetime. After DELETE + recreate, even when ID and numeric revision repeat, the prior create-event identity no longer matches and an old token is rejected.
- It does not protect against privileged SQLite history rewriting, authenticated external provenance, malicious shared filesystem modification, commit-outcome uncertainty, or actions by callers using the unfenced legacy `put` interface. A post-COMMIT error is **not proof of rollback**; there is no automatic replay/retry. Input drift at the clock boundary is rejected before commit.

Focused tests `tests/test_memory_generation_fenced_cas_run533.py` cover 18 authored parametrized cases: normal next-revision update, token replay, ABA delete/recreate, cross-handle restart, two concurrent writers, forged token types/digests, coherent row/history tamper, invalid/reentrant clock rollback, missing row and event bound.

## Package B — Offline WAV fixture pipeline

- `src/ark/offline_wave_energy_pipeline.py`: `preview_offline_wav_energy` combines the preexisting strict RIFF/WAV PCM inspector, bounded signed-mono16 converter, deterministic linear resampler and amplitude-region analyzer. Input is explicitly supplied fixture **bytes**, not a microphone stream; output contains source hashes and bounded region metadata but **no raw PCM**.
- Exact WAV metadata/source digest and converted/resampled PCM byte digests are checked at each stage. The fixed output rate is 16 kHz, the analysis frame is 20 ms, and RMS threshold is explicit. Regions are **energy activity estimates, not VAD, wake words, ASR, speaker identity, consent or notification eligibility**.
- Stereo/8-bit and mono/16-bit fixture paths supported within the strict underlying byte/duration limits. Oversize or unsupported media fails closed, no files are written, no audio is uploaded or logged.
- Linear interpolation intentionally does **not** provide production anti-aliasing; not a claim of production ASR audio quality or safe publication of potentially sensitive metadata.

Focused tests `tests/test_offline_wave_energy_pipeline_run533.py` cover 16 authored parametrized cases: deterministic mono16 activity regions, 8 kHz 8-bit stereo conversion, amplitude thresholds, malformed/oversized WAV, tampered request, result-authority mutation and repeatability.

## Write basis and CI evidence

- Initial work-basis PR #8 HEAD: `f6d62b6530715b6c0ea0cc772f3d5cfcda6976f5`.
- Memory source: `651c96226ce3b795bd6029eee778e5636f6df1b7`; test: `ff59171d79cf592954e16fff12edcd52e3508235`; new-test-only Ruff I001 import-order repair: `600ed22144ec68719873341e83a11d0da7ee9745`.
- WAV pipeline source: `e750887ee15c634f91f52d22bf1a72456f1e69f6`; tests: `ce78bdd71e1519f2428a825222b551035b258a0d`; new-test-only Ruff import-order repair: `361559a45a5d2e9b31755edae3cb5d8d605b1874`.
- Earlier PR #8 test run [41323330614](https://github.com/Iam-2squared/ark-ai/actions/runs/41323330614) **FAILED** at Ruff due to the two new test-file import blocks. Those are corrected without changing assertions or security semantics. Corrected [41323387209](https://github.com/Iam-2squared/ark-ai/actions/runs/41323387209) and [41323453131](https://github.com/Iam-2squared/ark-ai/actions/runs/41323453131) require exact-head GREEN verification before any PASS claim.
- Tests were authored, **not independently executed via local checkout/pytest**. CI outcomes are per exact commit, not transferrable to later documentation/checkpoint heads.

## Next gates / 今後の方針

1. Confirm the 6-platform CI on the final source+test HEAD and investigate any real test failure without weakening memory CAS/PCM privacy guards.
2. Evaluate whether an explicit capability boundary should wrap the new opt-in local memory writer before it can be used by the integrated JARVIS agent. No current PermissionGate or live ToolBackend integration is implied.
3. Join disconnected Planner/ToolRegistry/READ Journal mock recovery only after separate GREEN component evidence; no automatic UNKNOWN WRITE replay.
4. Extend local observation artifact retention/consent and startup lifecycle guards before any live microphone or tool action.
