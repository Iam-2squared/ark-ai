# ARK Run451 — isolated PCM activity regions and mono16 resampling

Status: **detached/offline fixtures only; NOT a multimodal integration PASS**.
Work-basis HEAD: f296fff8996b501aa4f21fd9257b97744dea01f1 (Run450 checkpoint).
Final source/test HEAD: 2d883a4b36e6eec6a7f237fa308b4e8190cd704f.
Repository lane: research/jarvis-foundations / Draft PR #8; PR #5 remains Draft.

## Source and exact saved bytes

| File | Final Git blob SHA-1 | Function |
| --- | --- | --- |
| src/ark/offline_pcm_activity_regions.py | 56710a4a266ff13fa89d5a171aa511ee3fe8074b | Offline signed-16 mono activity regions |
| tests/test_offline_pcm_activity_regions_run451.py | bfce57329f507bf35c74860877f59a8852ff3637 | Activity threshold, gap, type, budget, immutable result tests |
| src/ark/offline_pcm_resample16.py | 242fa1e2bdcd4e056c0cfeee187b1f6ba339a3e7 | Bounded mono16 integer linear interpolation |
| tests/test_offline_pcm_resample16_run451.py | 1d9ab4d8c7af13fe8aae106d89bc72d2653ae3c5 | Resampling, rejection, differential and raw-audio repr tests |

All four saved blob identities match the locally inspected/tested byte streams.
No previously frozen source, contract or evaluation fixture was modified.

## What actually works

**Activity regions.** Accepts exact bytes with a verified caller-supplied SHA-256,
signed 16-bit little-endian mono PCM, rates 8/16/32/48 kHz, bounded to 2 MiB
and 120 seconds. Uses 10/20/30 ms deterministic windows, integer mean-square
threshold comparison, configurable bounded silence bridging, minimum *actual*
active frames and at most 32 regions. Reports exclusive frame/sample offsets
and activity counts only. Final partial frames are evaluated against their real
sample count. It never returns original PCM, calls a microphone, recognizes
speech/speakers or authorizes a tool.

**Mono16 resampling.** Accepts exact bytes and caller-supplied SHA-256, bounded
to 2 MiB input/output and 120 s, with 8/16/22.05/32/44.1/48 kHz sample
rates. Output sample count is integer ceil of the rate ratio; integer linear
interpolation uses nearest-ties-away-from-zero rounding and last-sample
clamping. Same-rate output is bit-exact. Both input and output hashes are
reported; *raw resampled PCM is included in the returned result* and stays
sensitive. The result's dataclass representation explicitly excludes PCM
bytes (a privacy hardening change verified with a regression test).

Neither a digest match nor any requested rate establishes original recording
provenance, owner identity, retention permission, microphone consent, source
authenticity, speaker recognition, anti-alias quality, ASR quality or dispatch
authority. In particular, integer linear interpolation without low-pass
filtering is **not** a production-quality downsampling stage.

## Local validation and limitations

- Python 3.13.5 / pytest 9.0.2, isolated working directory, **90 passed**.
- compileall and Python AST parse: PASS; each new Python line <=100 columns.
- Separate seeded local probes: **1,200** segmentation oracle comparisons
  (unbridged contiguous activity) and **300** constant-signal resampling
  invariants: PASS.
- The resampling pytest includes **240** seeded input/rate differential
  examples within one test case; do not count these as 240 pytest cases.
- Source/test Git blob hashes were checked against local git hash-object.
- Full repository pytest/Ruff, Python 3.11/3.12, Windows, UI and all six CI
  matrix jobs are **NOT GREEN/NOT VERIFIED**. Ruff unavailable locally;
  GitHub clone blocked by container DNS. A no-side-effect Ruff B905
  cardinality hardening added strict=True to the activity-region zip.
- **Final source/test HEAD CI #1340, run ID 40318589714: QUEUED**
  when inspected. No equivalent manual workflow launched.
- Historical CI #1237 / run 40233213149 had Ubuntu pytest failures (known
  privacy-test expectation issue corrected previously); its three Windows
  jobs remained IN PROGRESS on the earlier inspection. Log retrieval for
  those in-progress Windows jobs returned HTTP 404 BlobNotFound, so a
  recovered/fixed Windows CI cannot be claimed.

## Safe future integration — NOT AUTHORIZED YET

1. Obtain exact-head GREEN for existing WAV inspection, PCM conversion and
   PCM activity, then for these two new modules; do not deduce later GREEN
   from locally passing tests or older successful commits.
2. Maintain independently retained owner, scope, consent and original PCM
   lineage across any future WAV -> mono16 -> resample -> region review.
   Caller-asserted hashes or sample rates are not origin witnesses.
3. Treat all audio and derived region timing as locally sensitive; no
   retention, external transfer, microphone activation or unconditional
   logging. Never pass a sensitive raw PCM result to a tool by default.
4. Keep speech/text interpretation separate from authority. Typed observation
   envelopes, trusted timestamps, revocation/retention fences, ToolRegistry,
   exact-type PermissionGate, issuer, durable occurrence and audit-before-action
   remain mandatory for any future effectful action; synthetic audio does not
   satisfy those gates.
5. Do not merge PR #8 or PR #5, open protected V2 final evaluation, create
   a real Candidate or weight, spend money, connect credentials/accounts,
   use external GPUs, invoke real tools or change frozen contracts.

This is reversible local-first groundwork. **Complete JARVIS: NOT_PASSED.**
