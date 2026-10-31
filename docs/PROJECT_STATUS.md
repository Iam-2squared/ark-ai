# ARK AI — Canonical Project Status

**LATEST — Run503 / 2026-10-31: four bounded, free-only source/test packages; Unicode-correct local Personal Context excerpts, redaction result custody, V3 review-packet path and independent digest/snapshot checks. JARVIS/V3 overall: NOT_PASSED.**

**Saved at:** **2026-10-31T21:21:23.105+09:00 Asia/Tokyo/JST** (runtime wall-clock sample immediately before this normal GitHub Contents API checkpoint write; not an attested or trusted time).

## LATEST — exact work basis and branch heads

- **JARVIS PR #8**: [Draft / unmerged](https://github.com/Iam-2squared/ark-ai/pull/8), branch `research/jarvis-foundations`. This invocation's initial work-basis HEAD `856d0f5a8b882e1ea5ec4a0bdc3fe05b78218f39` (Run502's latest verified source/document change). **Final source/test HEAD** `bab827b2a078e3b2bfa98048fdb12e3eeae231e5`. **Evidence / checkpoint write-basis HEAD** `464cf2fc0aba401004670ca402a46a46d1bdbc9a`. The **checkpoint-result HEAD** is the newly generated Contents API update and must be verified after saving, not guessed or embedded self-referentially.
- **V3 PR #5**: [Draft / unmerged](https://github.com/Iam-2squared/ark-ai/pull/5), branch `research/v3-learning-evaluation`. Initial work-basis HEAD `bc6263e87415c40961d66e6de9ca89e89b495d21`; **latest source/test and CI-fix HEAD** `5f20a00aa86c20dab76323a82279419a17c19f03`.
- **main**: `7a843f17eb96ed13d66f23b58b06406b3002e405` unchanged. PRs #5 and #8 were verified Draft, unmerged, and separately isolated immediately before this checkpoint.
- The previous [Run501 historical checkpoint](https://github.com/Iam-2squared/ark-ai/blob/0ea5b76b5290aa88f43578c5d3c3cede5ce0175b/docs/PROJECT_STATUS.md), uncheckpointed [Run502 technical evidence](https://github.com/Iam-2squared/ark-ai/blob/856d0f5a8b882e1ea5ec4a0bdc3fe05b78218f39/docs/JARVIS_RUN502_FAILURE_FIXTURE_RETENTION_V3_BUNDLE.md), and [Run503 technical report](https://github.com/Iam-2squared/ark-ai/blob/464cf2fc0aba401004670ca402a46a46d1bdbc9a/docs/JARVIS_RUN503_CONTEXT_PRIVACY_V3_PACKET_GUARDS.md) preserve the detailed chronology and source/test boundaries.

## NEW this invocation — four meaningful packages

1. **V3 authorization packet output path**: reject explicit `..`, symlink aliases (including directory ancestry), existing/dangling paths, missing parents, oversized names and derived path types before exclusive canonical JSON creation. Source/test commits `86bc7bdb0dd58077a2b64feff1d139361fa6de89` / `f00a4e9e88304a72b28c7bd9f9d69af9238db19c`. **11 authored cases**; PR #5 exact-head CI #1883 **6/6 GREEN**. This does not establish atomic filesystem custody.
2. **Privacy-safe Unicode lexical excerpt offsets**: source `src/ark/offline_context_search.py` maps expanded casefold text indices back to original codepoint positions, preventing invalid excerpts after characters such as `ß`, `İ`, and `ﬃ`. Source/test commits `865b2072ffe4fea0953975a35c5a2de503b79960` / `19473833d3cb9a330d8940ee5c50ed63e96f9eaf`. **7 authored cases**. Synthetic scope/consent/export denial retained.
3. **Detached V3 authorization-packet verifier**: new `src/ark/learning/authorization_packet_verify.py` independently checks exact unapproved snapshot, canonical full-packet bytes/SHA-256, internal packet SHA, field carrier stability and explicit no-authority witness. Source/test commits `24ee0cf40f475b89a06d6354f9276fabbecf5348` / `8f61a1697090e7ac7cf9e965c15b3d6be0556349`; minimum Ruff-only test line wrap `5f20a00aa86c20dab76323a82279419a17c19f03`. **19 authored cases**. Verification does NOT grant human consent, spend, training, Candidate, protected V2 evaluation or merge.
4. **Redaction receipt after-denial callback custody**: `src/ark/offline_context_redaction.py` now revalidates output identity, masked text, hashes and coverage after the final denial-only descriptor callback; prevents a False-returning getter from replacing already-checked output. Source/test commits `036b2c3632c5e774ab8c04b19bd3581c3e1ed336` / `bab827b2a078e3b2bfa98048fdb12e3eeae231e5`. **8 authored cases**. Masking remains neither erasure proof nor export permission.

**45 newly authored parameterized cases (11+7+19+8)** across four test files; these are defined-case counts, not independent local execution claims. Technical details and individual hazards are in the [Run503 evidence report](https://github.com/Iam-2squared/ark-ai/blob/464cf2fc0aba401004670ca402a46a46d1bdbc9a/docs/JARVIS_RUN503_CONTEXT_PRIVACY_V3_PACKET_GUARDS.md).

## CI / evidence — exact heads at checkpoint read

- **V3 #1882 / 41199875663**, #1883 / 41199933620, and source-only **#1886 / 41200207584**: **6/6 GREEN each**, but only #1883 includes the output-path tests and not the new verifier tests.
- **V3 #1887 / 41200271013**: **6/6 FAIL** from a single Ruff E501 in the new verifier test file. The line was wrapped without weakening any assertion. **V3 latest corrected source/test #1890 / 41200458143**: **6/6 GREEN** confirmed individually on Windows and Ubuntu, Python 3.11–3.13.
- **JARVIS earlier Run502 #1881 / 41199388605**: **6/6 GREEN** for the prior work-basis HEAD, not Run503 code.
- **JARVIS Run503 latest source/test #1889 / 41200397063**: **3/6 GREEN, 0 FAIL, 3 Windows jobs IN PROGRESS** at most recent job-level check; CI **NOT yet final GREEN**. The docs-only #1891 / 41200591755 was **6/6 IN PROGRESS** at the same checkpoint read, not final GREEN.
- **Independent local pytest / Ruff**: **NOT VERIFIED**; local `git ls-remote` failed due to DNS resolution of `github.com`. Only GitHub Actions commit-scoped results support CI claims. No equivalent manual workflow rerun launched.

## Frozen boundaries, blockers, authorization

- Frozen verified blobs unchanged: Memory `src/ark/memory/contracts.py` = `b6e93821ecd69270a7634aceb20775dc36e9953c`; Agency `src/ark/agency/contracts.py` = `13f1bb725f9c2c783e29402ca4a6e0f86b850ef9`; V3 `docs/v3/CONTRACT.md` = `b44f7b0e7e619c225ab662ed9c1fc8deae2b1e23`, checksum artifact = `176154514bd6be22685ca0555bc682c3bd8d45dc`. Frozen V1/V2/Local UI/Launcher evidence and final evaluation remain untouched in scoped work.
- **ZERO new paid or potentially billable services/compute**, no external GPU, API spend, new credentials, user-device action, real ToolBackend dispatch, microphone/camera capture, private dataset use, real Candidate/adapter generation, protected V2 final-evaluation opening, automatic promotion, destructive operation, protected contract change or main merge.
- Local checksums, synthetic time, snapshots and denial-only receipts are NOT upstream provenance, human consent, independently attested trusted time, external billing authorization, side-effect completion, deletion certification or a model PASS. Recovered UNKNOWN WRITE must never be automatically retried.
- V3 real training remains blocked on approved data/provenance/contamination/rights, immutable model and tokenizer bytes/revision, runtime and export identities, explicit spend authorization and hardware billing ceilings, protected evaluation gating, reproducibility and manual approval.

## Next plan / 今後の方針

1. Confirm exact-head **PR #8 #1889/#1891** job-level matrix and fix only concrete failures; do not reuse older CI, weaken tests or start redundant workflows.
2. Proceed with **Memory CAS/expiry/coherent snapshot**, **Planner UNKNOWN WRITE quarantine/recovery**, **immutable ToolRegistry and exact PermissionGate**; connect mock-only components only after relevant exact-head GREEN gates.
3. Harden trusted-clock audit-before-action, occurrence/replay prevention, proactive Scheduler restart readiness and privacy-safe Personal Context consent/revocation. Keep disconnected Observation fixtures separate from real capture.
4. Continue V3 **free-only identity, path, packet, provenance and reproducibility** guards without crossing real Candidate generation, paid compute, protected V2 opening, promotion or main merge gates.

---
**Single Run503 canonical checkpoint update after meaningful source/tests/evidence. Previous checkpoints and frozen evidence remain in pinned Git history.**
