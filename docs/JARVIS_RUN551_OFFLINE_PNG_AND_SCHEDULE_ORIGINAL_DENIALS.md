# Run551 — Detached PNG source custody and restart-scheduler denial baselines

**Scope:** Isolated, reversible, mock/local-only work on Draft PR #8; **not** an external ToolBackend, camera, consent source, trusted clock, proof of historical action, notification, or exact-once effect. No changes to frozen Memory, Planner, V1/V2/UI/Launcher or V3 contracts. No user hardware, external GPU, billable resource, training, protected evaluation or main merge.

## 1. Detached PNG scanline report

- Implementation `src/ark/offline_png_scanlines.py`: source commit `f9cf9c9a099d204983b32621350d7ca9db187b20`.
- Regression `tests/test_offline_png_scanlines_reentrant_custody_run551.py`: test commit `74aaf3589815f4a0f124999a88e4fe7ef97fc244`, **13 newly authored parameter-expanded cases**.
- `verify_offline_png_scanlines` now pins the *caller-supplied IDAT request* and the detached digest-only audit across the complete verification, including every denial-only report getter. It rejects reentrant edits to privacy/file digest/bytes/geometry even when the getter still returns `False`.
- The five denial-only `OfflineScanlineAudit` class property descriptors are compared with the import-time originals, not a baseline captured after an untrusted callback. It rejects preinstalled false-only substitutes, last-getter changes to the report or caller bytes, and late descriptor swaps.
- The existing deterministic zlib/PNG scanline decoder, format budgets, pixel digest calculation, non-release of decoded pixels and synthetic fixture boundaries are unchanged. This neither authenticates a PNG container nor proves filesystem race resistance, camera identity, consent, or authority to release images.

## 2. Offline schedule restart

- Implementation `src/ark/offline_schedule_resume_review.py`: source commit `71824b0838c82347fcb02b47a0fbed179cc99dbd`.
- Regression `tests/test_schedule_resume_original_denial_descriptors_run551.py`: test commit `a0603c2a00438711678063e5c4e26f643aad8def`, **9 newly authored parameter-expanded cases**.
- Quarantine witness authenticity and all five detached due-preview denial properties now use import-time original descriptors; replacing them before the restart review or during the first SQLite inspection is rejected even if replacement callbacks return `False`.
- Already existing retained witness, occurrence-index identity, independent preview fingerprint, time-floor, double read and final witness verification remain unchanged. Caller time and independently retained hash are untrusted; no automatic replay, action, notification, or cursor mutation is permitted.

## Evidence classification

The 22 counts above are authored test cases, **not local pytest PASS evidence**. GitHub Actions are separate exact-HEAD evidence:

- PNG test HEAD `74aaf3589815f4a0f124999a88e4fe7ef97fc244`: [CI 41404795878](https://github.com/Iam-2squared/ark-ai/actions/runs/41404795878). At preparation, Ubuntu 3/3 GREEN, Windows 3 jobs still in progress; do not claim 6/6 until finished.
- Schedule test HEAD `a0603c2a00438711678063e5c4e26f643aad8def`: [CI 41405222745](https://github.com/Iam-2squared/ark-ai/actions/runs/41405222745). At preparation, six jobs in progress; do not claim 6/6 until finished.
- Pre-existing Run550 checkpoint-less source HEAD `84621570b30cc4bc5e9aa0c6d9551458dddae89b`: [CI 41403540040](https://github.com/Iam-2squared/ark-ai/actions/runs/41403540040), all six Windows/Ubuntu Python 3.11–3.13 jobs GREEN when checked.

## Remaining boundary / Next plan

Close latest exact-head CI before claiming validated integration. Next tackle disconnected Planner FAILED/BLOCKED recovery, registry-bound READ history, manual-only Memory COMMIT-UNKNOWN reconciliation, retained witness custody, scheduler occurrence uniqueness and privacy revocation floors. Never infer actual consent or execution from a locally recomputed digest.
