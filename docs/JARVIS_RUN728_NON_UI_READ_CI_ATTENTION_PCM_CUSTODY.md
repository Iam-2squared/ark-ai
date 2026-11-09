# ARK AI — Run728: detached READ CI correction, proactive digest authority and private PCM preaccess

**Recorded:** 2026-11-09 12:58:03 JST (administrative wall-clock, not trusted action-clock evidence).
**Branch:** `research/jarvis-foundations` / Draft PR #8, still unmerged.
**Initial work basis:** `71df9c14e6617995230465e8caccdb846a1afa70`.
**Scope:** FREE-ONLY, non-UI, disconnected synthetic/mock data. No hardware, network executor, paid provider, training, protected V2 final evaluation, candidate promotion, PR #5/#9 edits or main merge.

## A. Real Run727 regression repair, without relaxing source checks

[Run727 exact checkpoint CI #42553147731](https://github.com/Iam-2squared/ark-ai/actions/runs/42553147731): **6/6 FAIL**. Actual Ubuntu 3.11 test log: **11,456 PASS / 8 FAIL / 1 SKIP**. All eight assertions in four inherited detached READ recovery test files expected a substituted SHA-256 callback to execute (previously once or during a late hook injection). Run727 source now imports and pins the original SHA identity and rejects such a callback *before* it can process a private READ graph.

- [`f1e6835`](https://github.com/Iam-2squared/ark-ai/commit/f1e68358c5185b604d03d0806cd294e321124484): result constructor callback never reached; injected and executed collections both empty.
- [`dc5481e`](https://github.com/Iam-2squared/ark-ai/commit/dc5481ea964e642b985c3370c895de9b4900e0d1): result slot injection never reached.
- [`4607e6e`](https://github.com/Iam-2squared/ark-ai/commit/4607e6eea7168b1c71a8d474e341f37ce041eb6e): input-step slot trap never installed by replaced SHA.
- [`ea6b84d`](https://github.com/Iam-2squared/ark-ai/commit/ea6b84d39c30dcf8a74a719e3d8db7371e395812): denial property swap callback never invoked.

The READ production implementation is **unchanged in this run**; no real READ dispatch, automatic replay or external outcome attestation. [Corrected-source CI #42558310308](https://github.com/Iam-2squared/ark-ai/actions/runs/42558310308) had **3/3 Ubuntu GREEN**, Windows jobs **IN PROGRESS** at an observed read; do not extrapolate this to a 6/6 result.

## B. Detached proactive attention: digest/protocol identity

[`d9a870a`](https://github.com/Iam-2squared/ark-ai/commit/d9a870a75f14e93fb754a18c99b699b5bb05bf10) pins import-original `hashlib`, `json`, SHA-256 and `json.dumps`, hash-domain and SHA-regex objects, and exact clock/marker cap objects before synthetic policy/history field reads. The existing repeatedly called authority check now rejects replacement after callbacks as well. [Nine new parameter-expanded regression cases](https://github.com/Iam-2squared/ark-ai/commit/8342bcc8f019a906bddab1ab1b6483bf81d97f77) require no hostile SHA/JSON callback invocation, even under equal-byte domain replacement, broader regex or larger caps; a clean mock preview remains non-authorizing. [Existing digest-injection test](https://github.com/Iam-2squared/ark-ai/commit/f58e737377b1d220cdc059062c9a96635010b76b) and [existing carrier injection test](https://github.com/Iam-2squared/ark-ai/commit/2563038fa7c21ed020a40ae0bfbba9ef868a0c7c) now require early denial rather than permitting the malicious hash callback to mutate inputs.

This is process-local review, not an OS sandbox, trusted clock, notification authorization, consent, or independent trigger provenance. [Intermediate CI #42558633091](https://github.com/Iam-2squared/ark-ai/actions/runs/42558633091) was **IN PROGRESS/QUEUED** at observed read. Latest source+tests on distinct later HEAD still require six-matrix validation.

## C. Disconnected 16-bit PCM fixture resampling: raw-bytes preaccess

[`c2bbd61`](https://github.com/Iam-2squared/ark-ai/commit/c2bbd61c2238ae40927373dc19e679375385ba16) adds a fail-closed import-original check for SHA-256, `struct.iter_unpack`, `struct.pack_into`, their module objects, rate/digest/buffer-size contracts, rounding function, and receipt constructor/field/lookup descriptors **before raw private PCM reaches any of these codecs**. Rechecks occur before output hashing, result construction, field access and return. No waveform acquisition or remote processing. [Twelve new authored parameter-expanded tests](https://github.com/Iam-2squared/ark-ai/commit/c775ea3775005d825d19993d675a6a774ce04f06) cover eleven hostile substitutions plus unchanged bit-sensitive deterministic output/hidden `repr` bytes.

Source and tests are intended as an additive, reversible observation-fixture guard. No anti-alias filtering, production ASR, identity inference, user privacy approval, microphone permission or remote inference is implied. [Source/test CI #42558877877](https://github.com/Iam-2squared/ark-ai/actions/runs/42558877877) was **QUEUED** at observed read. No clean latest-HEAD six-matrix PASS claim.

## Independent review / next boundaries

Read-only source inspection identified an additional review candidate in `src/ark/proactive_synthetic_continuity_review.py`: the `_digest` callback is intentionally replaceable in existing bounded-row and reentrant fault-injection tests, and private prepared-trigger SQLite values flow into it. This run does **not** narrow or silently disable those test seams. Any future preaccess redesign must retain explicit bounded-row/phase test coverage, deny-before-private-read semantics and exact source/CI evidence. Separately, Memory event-prefix and append/CAS outcome integrity remain local SQLite witnesses rather than authenticated writer identity, approval or a trustworthy external clock.

**Evidence rule:** Only source and GitHub save commits listed here are confirmed. Exact final checkpoint-result HEAD test verdict is pending, and all numeric test counts are authored test parameterizations unless explicitly labeled a completed CI result. V1/V2/Local UI/Launcher freezes, protected V2 final evaluation and V3 Contract 1 are unchanged. All PRs #5/#8/#9 remain Draft/unmerged; #9 UI remains paused. **ARK overall NOT_PASSED.**
