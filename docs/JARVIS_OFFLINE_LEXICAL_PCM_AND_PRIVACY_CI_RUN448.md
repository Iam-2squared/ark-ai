# Run448 — Detached lexical retrieval, bounded WAV PCM inventory, and CI regression repair

**Scope:** `research/jarvis-foundations`, Draft PR #8; work-basis
`6ae21d16841360a137c7448936c743774e9d976b` (Run447 checkpoint).
**Final source/test HEAD:** `6a6f05650b67cbafaf163037560658e2fc0f3261`.
**Change inventory:** GitHub compare confirms five normal-Contents commits, four
added source/test files, one existing test modified, no existing executable
source altered or deleted. All four new Git blob SHAs independently match
the isolated Python 3.13.5 test-input bytes.

## Package A — Real, bounded in-memory local lexical search

`src/ark/offline_text_index.py`, Git blob
`f83c98559ba35a9acd3332823151798f35ab9b19`;
`tests/test_offline_text_index_run448.py`, Git blob
`f14119e85fdc7e8903d0b239400b698292de3f7e`.

- Pure, disconnected `search_offline_text(OfflineIndexQuery)`, no import
  dependency on unverified Run447 chunking/Memory or other JARVIS modules.
- Hard bounds: 1–32 exact document objects, 65,536 UTF-8 bytes each,
  131,072 corpus bytes total, 30,000 total lexical tokens; 512 query
  bytes, 1–16 query tokens, at most eight result identifiers.
- Strict UTF-8, SHA-256 original document/query checks, exact owner and
  scope marker shape, no mixed scope, no duplicate IDs, caller-asserted
  complete sorted membership. `NFKC`/casefold Unicode lexical tokens.
- Deterministic integer rank: 100 points per distinct matched query token
  plus min(term-frequency, 8); descending score then document ID tie break.
  Output contains only identifiers, scores, hashes, and scan counts.
  Never returns document text, snippets or credentials.
- Local digest of document membership and rank is for *consistency only*.
  The caller can forge its own hashes and scope markers: NO trusted
  identity, independent membership witness, revocation, consent,
  retrieval authorization, encryption, retention, or privacy guarantee.
  Search must not be connected to live Memory/LLM context without all gates.
- **38 isolated Python 3.13.5 pytest cases passed** (positive ranking,
  Unicode, empty/no hits, tie, score cap, limits, identity mismatch,
  source modification, missing/duplicate membership, invalid Unicode,
  carrier replacement, no returned raw text).

## Package B — Actual canonical PCM WAV byte inspection without audio export

`src/ark/offline_pcm_wav.py`, Git blob
`08a69ff9e676acf23704b8b0dc261a45fc1b2982`;
`tests/test_offline_pcm_wav_run448.py`, Git blob
`6156dec2c5edf6cace3d71b586557d00c34268b2`.

- In-memory `inspect_local_pcm_wav(OfflineWaveRequest)` parses real
  caller-provided RIFF/WAVE bytes. No microphone, disk, network, audio
  playback, ASR, speaker identification, or hardware capture.
- Strict canonical subset only: little-endian `RIFF/WAVE` with exactly
  `fmt ` then `data`, PCM encoding 1, 16-byte fmt, 1–2 channels,
  sample rates 8,000–48,000 Hz, 8/16/24/32-bit integer PCM, aligned
  nonempty frames and exact byte-rate/width. No `LIST`/hidden metadata,
  unknown/reordered/duplicate chunks or trailing data.
- Hard maximum input size 8 MiB, at most 120 seconds. Exact RIFF length,
  required zero pad for odd data, input SHA-256 and PCM-content SHA-256.
  Result exposes channel count, rate, bit depth, frame count, duration
  integer quotient and remainder only — never raw PCM bytes.
- Validation intentionally does NOT prove speech, provenance, consent,
  image/audio rights, or safe use. Additional WAV layouts/encodings are
  rejected rather than silently accepted. The request identity hashes
  are untrusted caller assertions.
- **42 isolated Python 3.13.5 pytest cases passed**, including deliberate
  malformed chunk, padding, checksum, unsupported format/rates/widths,
  partial frames, 2-minute boundary, and no-audio-output cases.

## Package C — Existing privacy regression; confirmed real CI failure

At Run448 inspection, GitHub Actions **#1237**
(run `40233213149`, code HEAD `698eab6942c4e7f35c47c2abec7e9985d0669c54`)
had three completed Ubuntu jobs marked **FAILURE** and three Windows jobs
still **IN PROGRESS** in `pytest`. Ubuntu 3.11 and 3.13 raw job logs
both showed the exact two failed assertions in
`tests/test_privacy_cross_process_veto_projection_run434.py:101`:
`assert len(checks) == 2`, actual `len(checks) == 1`. The reported
3.11 suite summary was **2 failed, 2931 passed, 1 skipped**.

Cause: the second `assert_not_revoked` attempt correctly raises before
the wrapper appends its successful-clearance marker. A single
`checks` list could not represent both *attempted veto reads* and
*successful clearances*. Thus the old assertion was conceptually wrong
even though the privacy path properly denied the revoked scope.

Minimal test-only correction (Git blob
`61b197bdf0728c25387a55a9f9beb7082836b418`):
track `attempts` **before** the native check; track `clearances`
**after** native success. Assert exactly two attempts, exactly one
successful clearance, and the existing fail-closed `revoked` exception.
The source logic, SQLite schema, permission scope, denial condition and
review gates are unchanged. This is source-level/log-backed diagnosis,
**not yet a new full-repository CI PASS**.

## Verification, CI, limitations

Locally, `PYTHONPATH=/mnt/data/ark_run448/src python -m pytest -q
/mnt/data/ark_run448/tests` yielded **80 passed** (38 lexical + 42 PCM);
`python -m compileall -q` passed; all four new Python files use
lines <=100 characters. GitHub-returned blob SHA-1 matches independently
computed local `git hash-object` for all four exact tested files.

The old privacy regression correction is code-reviewed against CI logs,
but isolated testing above **does not execute** that integrated test.
Local `ruff` is unavailable and full GitHub checkout is blocked by the
container DNS resolver; no full repository lint/pytest, Python 3.11/3.12,
Windows, packaging/UI or all-six-job GREEN is asserted.

Source/test HEAD #1319 (run `40298027737`) was **QUEUED** at the first
check. Separate earlier #1315–#1318 for intermediate HEADs were also
QUEUED. At sampled inspection there were **81 QUEUED and 6 IN PROGRESS**
GitHub Actions workflow runs; we did not rerun, cancel, downgrade checks,
open frozen evaluations, or dispatch billable external compute.

## Next plan

1. Watch exact-head #1319 and newer technical/checkpoint CI; investigate
   any additional failures through the actual job logs. No GREEN until all
   relevant jobs complete successfully.
2. Keep lexical index detached from real Memory, its Run447 chunks and
   Personal Context until trustworthy independent inventory, revocation,
   retention, consent and exact-head GREEN exist.
3. Keep PCM fixture parsing detached from any real microphone/ASR,
   private data, diarization, external export or ToolBackend. Later link to
   synthetic transcript *metadata* only after lower-level proof is GREEN.
4. Continue independent Memory CAS/expiry and planner recovery research,
   without ever automatically replaying UNKNOWN/RUNNING or reserved PENDING
   writes. Preserve all frozen V1/V2/Local UI/Launcher and V3 Contract 1
   evidence; PR #5 Draft/NOT_PASSED, PR #8 Draft/unmerged; no new paid
   services, real Candidate, protected evaluation, main merge or external actions.
