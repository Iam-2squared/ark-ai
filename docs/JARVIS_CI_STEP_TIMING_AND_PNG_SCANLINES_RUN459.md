# ARK Run459 — truthful CI activity timing and bounded synthetic PNG scanlines

**Branch/PR:** `research/jarvis-foundations`, Draft PR #8; PR #5 remains Draft/unmerged.
**Work-basis HEAD observed at start:** `e7bba49168119be69a648d07a45ca8ba614d3429` (Run458 source/test, preceding the Run459 writes).
**Final source/test HEAD:** `47d7672cc06232341a29a2b934b199dbe09155b1`.
**Time observation:** 2026-10-27 approximately 04:07 Asia/Tokyo/JST; ordinary local clock, NOT a trusted timestamp, user consent or reviewer approval.
**Status:** two independently tested free-only packages; exact-head six-cell GitHub CI **NOT GREEN / QUEUED**.

## Work package 1 — correct false-positive stalled-pytest classification

- Updated `scripts/ci_queue_review.py` (Git Blob `1777c11f07e922e3e0b2e4c15a896707a12cebb6`).
- Added `tests/test_ci_queue_review_run459.py` (Git Blob `8d778f46cc11bf624664f516cb4f94f46b0622ef`).
- The previous helper classified a pytest step as stale using its **run creation age**. A run queued for hours but executing pytest for 30 seconds would be incorrectly classified as stale. Run459 now uses the individual step's `started_at` and the running workflow's `run_started_at`; queued runs still age from `created_at`.
- Missing activity timestamps are reported as explicit unknowns, not silently promoted into aged/stuck; malformed, future or precreation timestamps are rejected. The output is a read-only *elapsed-time diagnostic*, not proof of a deadlock, CI failure, runner authority, billing permission, job cancellation approval, or GREEN status.
- Local independent regression **21 PASSED**, including stale vs recently started pytest, queued vs active run age, unknown timestamp treatment, invalid carrier types, impossible times, inconsistent statuses and no implied CI authority.
- No jobs were started, retried or canceled by this audit. The existing CI workflow and matrix gate are unchanged.

## Work package 2 — detached bounded IDAT/zlib scanline verifier

- Added `src/ark/offline_png_scanlines.py` (Git Blob `8cc2ae951de60df4f1f9ff02bb58fc67dcddba54`).
- Added `tests/test_offline_png_scanlines_run459.py` (Git Blob `dac6ec960b9f2bc34ab34ab0d6f7cc1ecfb9667e`).
- Checks exact-type synthetic IDAT bytes and digests, 8 MiB compressed source limit, image dimensions <=4096 per axis, <=4,194,304 pixels, and <=40 MiB decompressed scanline budget.
- Accepts only noninterlaced row format constraints encoded by supplied geometry, supported PNG color types/bit depths, correct complete zlib stream and exact decompressed row count. Rejects trailing compressed data, missing trailer/Adler32, expansion bombs, invalid row filters, and out-of-palette indexed pixel references. Reconstructs PNG row filters 0–4 **only in temporary private memory** and returns hash/count metadata without raw pixels.
- Local independent regression **37 PASSED** (one test initially exposed an incorrect *test fixture expectation* for Paeth; the fixture was corrected before the final 58/58 PASS). A separate deterministic 2,000 mutated-IDAT check rejected 1,991; 9 were admitted as still-valid synthetically encoded streams; zero unexpected exceptions. All counts are local, not GitHub CI.
- This is **not connected** to the Run457 PNG framing inventory. It accepts caller-supplied metadata and hash; no binding to actual PNG chunks, authenticated image origin, camera, image semantics, consent, observation, Memory or Tools. No authorization is established; successful zlib/scanline validation is not an image-provenance or privacy PASS.

## Test provenance and CI barriers

Python **3.13.5**, pytest **9.0.2**, isolated synthetic local source/test files: **58 PASSED** (21 + 37), `compileall` PASS; source/test line lengths <=100. Saved GitHub Git Blob SHA values were independently compared against the exact files under local `git hash-object` after normal GitHub Contents writes.

Natural PR-triggered CI observed at 2026-10-27 ~04:07 JST, no manual job dispatch:
- `#1391`, Run ID `40383198527`, final CI audit regression HEAD `d09163d015d2db57cf203aefa5566d83b3816423`: **QUEUED**.
- `#1392`, Run ID `40383581000`, PNG scanline implementation HEAD `f6942a951137168b2fb5d6ecf8570ab08f9df241`: **QUEUED**.
- `#1393`, Run ID `40383680459`, final source/test HEAD `47d7672cc06232341a29a2b934b199dbe09155b1`: **QUEUED**.
- Earlier Run458 `#1390` (Run ID `40381657473`) also **QUEUED**. Historical #1244 jobs include three genuine Windows `Run pytest` steps observed IN PROGRESS using raw job metadata and exact started timestamps. Historical Linux failures do not establish current failures. No exact latest-head all-six GREEN, whole-repo pytest, Ruff, Windows, Python 3.11/3.12, packaging/UI smoke or CI SUCCESS has been obtained.

## Frozen boundaries and priorities

V1/V2/Local UI/Launcher evidence, Memory V1, ActionAudit V1, frozen V3 Contract 1 and protected evaluation boundaries unchanged. PR #5 and PR #8 remain Draft and unmerged. No paid APIs/GPU/external compute, real Candidate/weights, protected V2 final opening, secret/account, user personal bytes, camera/microphone, actual user approval, destructive operations, real Tool execution, automatic promotion or main merge.

1. Observe naturally executing exact-head CI and repair authentic failures without lowering gates or duplicating runs; prioritize historical Windows pytest runner bottleneck evidence.
2. Keep detached scanline verifier unintegrated until its own code/tests and PNG framing dependencies obtain exact-head GREEN, then design an explicit digest- and metadata-bound fixture adapter with privacy review.
3. Continue Memory CAS/coherent snapshots, Planner recovery/unknown-WRITE fencing, trusted-clock and registry-bound PermissionGate in safe independent lanes.
4. Demand independent source identity, user consent and authorized retention before any real Observation/Memory ingestion. Neither local hashes nor elapsed-time heuristics prove identities or authorization.
