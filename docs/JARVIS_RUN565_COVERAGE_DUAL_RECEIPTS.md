# Run565 — free-only multimodal coverage and durable receipt binding

**Work basis:** PR #8 `research/jarvis-foundations` at `d5e0ff5bcbe7f6e5c0e21c7e7fd80de13d98bdca`. Baseline [GitHub CI 41523942891](https://github.com/Iam-2squared/ark-ai/actions/runs/41523942891) completed **SUCCESS / 6 jobs**. PR #5 remains Draft and isolated. No main merge.

## 1. Detached observation/transcript coverage (source + regression tests)

[Source commit `9730bc8e`](https://github.com/Iam-2squared/ark-ai/commit/9730bc8e68310c73c2663aff33f33bd8dcca1a91) adds `src/ark/offline_transcript_coverage.py`. [Tests `15ba1431`](https://github.com/Iam-2squared/ark-ai/commit/15ba1431e4fb86da2b9397a175e06f3a64e51d4e), import-order correction [`1b60724d`](https://github.com/Iam-2squared/ark-ai/commit/1b60724d323f993bd0bef639f6e5233b7320fb84).

The passive reviewer consumes **only explicit caller-provided** bounded PNG/WAV fixture bytes, exactly typed transcript segments and five retained digest claims. It invokes the separately existing pair and transcript validators twice and checks the exact shared audio/observation identity. It produces the transcript coverage in frames: covered, leading/interior/trailing gaps, a floor-truncated parts-per-million ratio, and a domain-separated SHA-256; no text/pixels/PCM leave the report. All original denial-only authority properties remain false, and input carrier epochs are rechecked. Empty/misaligned intervals and counterfeit retained claims fail closed.

**Limitations:** This is timeline accounting, NOT speech/silence classification, ASR, transcript correctness, sensor identity, trusted acquisition time, authenticated consent, or permission to access/disclose/act. The independently retained origin of hashes is **not established** by comparing caller-provided claims. The new code is reversible while PR #8 is Draft.

## 2. Memory ambiguous COMMIT dual receipt binding

[Source `44a84084`](https://github.com/Iam-2squared/ark-ai/commit/44a840843d8a49a246f32741203e621f3657249b) and [tests `d016418a`](https://github.com/Iam-2squared/ark-ai/commit/d016418afbab5aa0ff2550aed8f66f52c1a29193) correct a narrow evidence-integrity omission. The previous reconciliation digest included the first SQLite triage receipt SHA but **not** the second independent CAS outcome reviewer receipt SHA. The new retained read tuple contains **both** receipt digests, verifies their exact 64-hex shapes, and makes two-pass drift of either one a rejection. The public result remains manual-only with automatic retry and write denied.

**Limitations:** Two reads do not establish cross-transaction atomicity, historical writer attribution, trusted clock, human consent or exactly-once external effects. This remains read-only SQLite triage, never an automatic COMMIT retry.

## 3. Scheduler due-prefix receipt custody

[Source `b24409e8`](https://github.com/Iam-2squared/ark-ai/commit/b24409e83b46e4cd0fb9abb9373e01bf409c4a6e) and [tests `f85ef924`](https://github.com/Iam-2squared/ark-ai/commit/f85ef924f1694b7206f15597ce0ef41fa0a17078) bind the separately reviewed due reservation **prefix receipt SHA** to the restart digest. The digest namespace moves from `ARK-due-restart-triage-v1` to `v2` because its canonical payload changes. Malformed prefix SHA values are refused before output. Previous behavior only included prior/current count+tip and state, omitting the exact inspected-prefix receipt. Tests demonstrate binding, including the difference between an unchanged local tip and a caller-fabricated digest; this is not historical authentication.

**Limitations:** No scheduler timer/notification, trusted wall time, user-consent proof, tool execution, replay authorization, or independent external effects.

## CI/evidence handling

The pre-change [Run564 checkpoint CI 41523942891](https://github.com/Iam-2squared/ark-ai/actions/runs/41523942891) is 6/6 GREEN. Initial Run565 [CI 41530958040](https://github.com/Iam-2squared/ark-ai/actions/runs/41530958040) failed Ruff on an import order in the new coverage test; corrected without weakening runtime semantics. The source+test HEAD for all three packages is `f85ef924f1694b7206f15597ce0ef41fa0a17078` (before this note); [CI 41531644507](https://github.com/Iam-2squared/ark-ai/actions/runs/41531644507) was **QUEUED at preparation**, NOT a PASS. This document makes no claim of independent local pytest success. Subsequent CI state must be verified at its exact commit and six job conclusions.

Frozen Memory/Planner/V3 contracts and V1/V2/Local UI/Launcher evidence are unchanged. No paid/external GPU compute, service charge, new credentials, real Candidate/weights, protected V2 evaluation, promotion, ToolBackend dispatch, hardware operations, destructive action or main merge. **ARK/JARVIS/V3 NOT_PASSED.**
