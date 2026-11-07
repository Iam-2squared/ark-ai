# ARK JARVIS detached PCM activity and binary inventory — Run449

Saved at: **2026-10-26T18:52:00+09:00 JST**, ordinary wall-clock observation only, not trusted-clock, user consent, or external attestation.

## Exact work basis and scope

- Prior canonical status checkpoint HEAD: `5ede1f5ee13b4da83dd19245eb1dd1119d198f92` (Run448).
- Draft PR #8 branch: `research/jarvis-foundations`, remains unmerged.
- Final source/test HEAD before this document: `3ea6bfc42e74d7329d2ba0d1bba66cd44e9fa7a5`.
- Four normal GitHub Contents writes, no overwrite or frozen-contract modification.
- The generated document's own commit SHA is only known after GitHub returns from this write.

## Package A — disconnected integer PCM amplitude windows

`src/ark/offline_pcm_activity.py`: Git blob `b023b64ca89f02dde7b931a98227cfaeb844122b`.
`tests/test_offline_pcm_activity_run449.py`: Git blob `f329e04afaefe09791e604ad08cbf8fd61b0b2f3`.

- Caller-supplied in-memory PCM; unsigned 8-bit and signed little-endian 16, 24, 32-bit; 1–2 channels; 8–48 kHz; integral 10–100 ms windows.
- Strict 2 MiB maximum; full-frame alignment, SHA-256 source integrity, 120-second bound, maximum 1,024 windows.
- Exact integer per-window peak and sum of squares; final partial window is covered; no ASR, model, microphone, speech/speaker detection, retained waveform, or external action.
- Separate owner/privacy hashes affect manifest; these are **untrusted assertions**, not proof of ownership or disclosure authority.
- **33 focused isolated pytest cases PASSED** on local Python 3.13.5.

## Package B — source-complete binary fixture receipts

`src/ark/offline_binary_inventory.py`: Git blob `efde2d483a2c2bf944f32dd663b18a295b644515`.
`tests/test_offline_binary_inventory_run449.py`: Git blob `9ca230d6f57c47e792b503dc57b2381637b2ef44`.

- No file reads or output bytes. An inventory covers each supplied byte once by bounded offset spans and domain-separated chunk digests.
- Strict 2 MiB source limit, max 64 chunks, max 65,536 bytes/chunk, immutable metadata receipt, no silent tail truncation.
- Re-verification requires caller-supplied full original source and separately retained source plus inventory digests. Missing, reordered, duplicated, shifted, or altered pieces fail closed.
- A caller can forge a matching source, receipt and retained hashes together. Independent durable/authenticated retention is not implemented, **no provenance/permission proof**.
- **25 focused isolated pytest cases PASSED** on local Python 3.13.5.

## Validation boundaries and CI

- Focused isolated local combined suite: **58 passed** (pytest 9.0.2, Python 3.13.5). Local `compileall` succeeded, all four files have no line exceeding 100 chars. GitHub blob SHAs for all four files equal the exact locally tested `git hash-object` values.
- Local repository clone unavailable due DNS resolution of github.com; local Ruff not installed. **No full repo pytest/Ruff, Windows, Python 3.11/3.12 or all-six-job GREEN**.
- New final source/test HEAD `3ea6bfc42e74d7329d2ba0d1bba66cd44e9fa7a5`: CI **#1325**, run ID `40302683430`, **QUEUED** on inspection. Prior Run448 CI #1321 (run `40298584099`) still QUEUED.
- No duplicate CI runs manually triggered, no changes to .github workflows, no runner polling in place of independent work.

## Security, privacy and frozen boundaries

Receipts and amplitude windows are synthetic/disconnected **local-first components only**. Window statistics may themselves reveal sensitive sound patterns; no export or persistence authorization. There is no real capture, authenticated issuer, trusted clock, user consent, production Memory, live ToolRegistry/PermissionGate/ActionExecutor, external outcome proof, or exactly-once external write.

Keep PR #5 and PR #8 Draft and unmerged; preserve frozen V1/V2/Local UI/Launcher, Memory V1/ActionAudit V1/V3 Contract 1, protected evaluation and V3 contamination/provenance/reproducibility/approval gates. No paid API/GPU, new credentials, training/Candidate, physical-PC action, main merge, irreversible operation or real Tool dispatch.

## Next plan / 今後の方針

1. Resolve actual CI queue and failures against **exact changed HEADs**; never treat local pass or historical Ubuntu success as six-job GREEN.
2. After dependent exact-head GREEN, consider attaching read-only PCM activity to the disconnected WAV bytes with explicit identity/consent/freshness checks; do not attach live microphone or assert ASR.
3. Keep source-complete byte inventory independent of local paths, with an independently retained membership witness before any durable multimodal import.
4. Continue Memory CAS/expiry/event proof, cross-store Planner WRITE quarantine/restart evidence, Personal Context privacy recheck, and V3 free-only guards on separate safe lanes.
