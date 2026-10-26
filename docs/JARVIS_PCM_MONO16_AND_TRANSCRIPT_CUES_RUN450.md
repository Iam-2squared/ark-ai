# JARVIS Run450 — disconnected PCM mono16 and transcript cue fixtures

This run adds **two real, bounded, standard-library offline transformations** on
explicit untrusted fixture bytes/text. They remain detached from live Memory,
microphones, audio sources, ASR, authenticated users, PermissionGate, Registry,
Planner, dispatchers, and OS/network side effects. Both are reversible
foundations; **Complete JARVIS remains NOT_PASSED**.

## A. PCM 8/16/24/32-bit to signed 16-bit mono

- **Source:** \`src/ark/offline_pcm_mono16.py\`, Git blob
  \`a11fca48e05f9e92cd40e0c6dba73ef90dd92fc2\`.
- **Tests:** \`tests/test_offline_pcm_mono16_run450.py\`, Git blob
  \`3c2a68bd24a0ce43236d208551d321903cfc719d\`.
- Pure integer conversion, little-endian PCM, unsigned 8-bit/other signed
  encodings, 1 or 2 channels, 8–48 kHz. Each input frame produces one signed
  16-bit mono sample. No resampling, float, file/network I/O or hidden
  truncation. Stereo mixing uses deterministic floor division; 24/32-bit
  inputs are shifted arithmetically down to 16-bit. There is no anti-aliasing
  or acoustic voice recognition.
- Exact caller-provided owner/privacy/source SHA-256 shape, source checksum,
  immutable carrier rechecks, input <=2 MiB, output <=2 MiB, duration <=120s,
  and full frame alignment are enforced fail closed. A domain-separated
  inventory hash binds owner, privacy, source, output, format and frame count.
  **Caller hashes are NOT real ownership, provenance or consent proof.**
- The result **contains RAW signed PCM bytes**: \`repr=False\` only reduces
  accidental display; it is NOT encryption, sanitization or permission to log,
  save, send, or use this sound in a real speech system. No microphone input.
- **41 isolated pytest cases PASS**; 800 additional seeded differential
  frame/bit-depth/channel probes match an independent integer reference.
  Returned identity and consent flags remain explicitly false.

## B. Detached text wake-cue recognition (NOT audio wake-word)

- **Source:** \`src/ark/offline_transcript_cues.py\`, Git blob
  \`96dfba8457a678e47180201885a87778bea1ec88\`.
- **Tests:** \`tests/test_offline_transcript_cues_run450.py\`, Git blob
  \`f099099faa9e48fa8e3bda71003f324a6fb6cfcb\`.
- Given explicit caller-supplied synthetic transcript text, recognizes one
  NFKC/case-folded exact-prefix cue followed by whitespace/punctuation
  separator, or an exact whole-utterance cue; rejects ambiguous overlapping
  cues, duplicate normalized phrases, invalid Unicode/control characters,
  forged format/IDs, inconsistent complete membership and checksum.
  Japanese cue + punctuation is supported. Concatenated speech without a
  delimiter is deliberately NOT treated as an instruction.
- Limits: transcript <=4 KiB, each cue phrase <=96 UTF-8 bytes, max 8 cues;
  canonical sorted cue membership required. Returns matched cue ID, bounded
  normalized command preview and domain-separated digests. The command
  preview is sensitive, excluded from \`repr\`, and MUST NOT be logged, sent
  outside the approved local context or executed. Any text may be untrusted
  adversarial input; a match **never authorizes any action**.
- **47 isolated pytest cases PASS**; 800 additional seeded text-boundary
  probes PASS. Speaker authenticity, microphone provenance, permission and
  consent flags remain explicitly false. There is no ASR, speaker ID,
  acoustic wake-word model, real world tool execution or prompt forwarding.

## Exact evidence and CI boundaries

- Initial checked Draft PR #8 HEAD / work basis:
  \`53beec69fa43e9d82f1c0ea5d5dcbaadb2fffa61\` (Run449 checkpoint).
- Final **source/test HEAD**:
  \`61f5546c08f472d2a86e5eadd3bce993cf5c11ad\`.
- GitHub compare confirms **exactly four normal Contents commits**,
  **four added source/test files**, no previous files deleted or modified,
  no frozen contracts changed. All four Git blob IDs above match local
  \`git hash-object\` of the exact tested bytes.
- Local Python **3.13.5 / pytest 9.0.2**: **88 PASSED** (41+47) in
  \`PYTHONPATH=/mnt/data/ark_run450/src python -m pytest -q
  /mnt/data/ark_run450/tests\`. \`compileall\` PASS, Python lines <=100 chars,
  1,600 seeded differential/boundary checks PASS.
- Local Ruff is unavailable, and full-clone GitHub DNS resolution has been
  unavailable. There is **NO proof** of full-repo pytest, Ruff, Python
  3.11/3.12, Windows, packaging/UI or full 6-job GREEN on these commits.
- Final source/test CI **#1331 / run ID 40311342964** was **QUEUED**
  at verified read. Any subsequent technical-document and checkpoint
  commit triggers separate CI; inspect their exact heads independently.
  No redundant workflow dispatch, cancellations, force pushes or relaxed
  regression gates were used.
- Historical CI #1237, run \`40233213149\`, has three completed Ubuntu
  FAIL jobs and three Windows IN PROGRESS jobs at inspected status. Older
  Ubuntu privacy regression cause was previously diagnosed and its test
  corrected in Run448; no conclusion about newer exact-head CI or Windows
  recovery is inferred from that patch.

## Safety and integration plan / 今後の方針

1. Resolve true latest-head CI failures and Windows job queue/hangs using
   actual logs. Do not integrate pending source with dependent in-flight
   modules or treat local PASS as production approval.
2. After lower-level exact-head GREEN, construct a disconnected end-to-end
   fixture test combining WAVE metadata, PCM conversion and amplitude stats.
   That composition must carry independently retained source/format/identity
   witnesses and have no microphone, ASR, or external disclosure.
3. Independently test that a text cue cannot bypass exact-type PermissionGate,
   registered ToolRegistry identity, fresh trusted clock, human authorization,
   audit-before-action, replay safeguards or WRITE quarantine. Treat parsed
   text as untrusted data, not a verified instruction.
4. Resume high-priority durable Memory CAS/expiry and Planner multi-WRITE
   quarantine/recovery only when their dependency evidence is GREEN.
5. Preserve V1/V2/Local UI/Launcher, Memory V1, ActionAudit V1 and V3 Contract 1
   frozen evidence and PR #5 Draft/NOT_PASSED. No paid/external GPU,
   Candidate training/generation, protected V2 evaluation, automatic
   promotion, sensitive data ingestion, material irreversibility, or main merge.

**ARK overall: NOT_PASSED.** Proven local fixture processing is NOT evidence
of a deployed, authenticated or autonomous JARVIS assistant.
