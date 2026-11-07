# ARK Run457 — offline PNG inventory and local source-identity continuity

**Branch:** \`research/jarvis-foundations\`; PR #8 Draft/open/unmerged, PR #5 Draft/open/unmerged.
**Work-basis HEAD:** \`f94ddcdcb35bcbb6cf637a7c9dca0ac800142ba3\` (Run456 checkpoint, checked before writes).
**Exact source/test HEAD:** \`b818535bdf0da27f561a6ba02f2d9a20097a2f81\`.
**Status:** two independent offline diagnostic components, locally tested; GitHub Actions exact-head six-cell GREEN **NOT VERIFIED**.

## Package A: strict synthetic PNG metadata inventory

- \`src/ark/offline_png_inventory.py\`, saved Git blob \`732d655106a11a2d33a4e2607fe3ca971658ea71\`.
- \`tests/test_offline_png_inventory_run457.py\`, saved blob \`11aa3ebea7e323a4063c29eddd4970f9f3bdc812\`.
- Exactly typed caller-provided bytes with SHA-256 inventory; PNG signature, canonical IHDR, permissible format/depth, width/height/pixel budget, chunk bounds, CRC32, optional indexed PLTE, consecutive bounded IDAT and terminal empty IEND are validated. Ancillary/private chunks (including EXIF/text), Adam7 interlacing, trailing data, unsupported bit depths or unbounded image payload are denied.
- No decompression, zlib/deflate stream validation, image decode, photo provenance, camera capture, identity authentication, consent, text/image semantics or disclosure authorization. An arbitrary IDAT byte sequence can pass *container* inspection; it must **never** be described as a validated or usable decoded image. CRC32 is not a signature. Inputs and pseudonymous scope/owner identifiers are hidden only from implicit \`repr\`, not explicit serialization.
- The output has image dimensions, color/depth, SHA-256 and chunk counts; not image bytes. Maximum input 8 MiB, maximum 4,194,304 pixels, maximum 64 IDAT chunks. No credentials, devices, network or external effects.

## Package B: detached local source metadata pin

- \`src/ark/disconnected_local_source_pin.py\`, saved Git blob \`1eb8f572b818c7bccc04a578749af8467cd952b2\`.
- \`tests/test_disconnected_local_source_pin_run457.py\`, saved blob \`a4291faf6c0b5cc6bcf3b8001859cb502c6bd6a6\`.
- Repeated, read-only \`lstat\` path checks bind an absolute normalized native Path, each ancestor directory's device/inode, and the singly linked regular-file device/inode/size/mtime. Relative paths, \`..\`, missing files, symlinks, hardlinks and changed parent/file identity are rejected; review requires exact retained pin type and checks reflective input drift.
- No database opened, read, mutated or created. This is **not secure-open**, cannot close a post-check TOCTOU race or independently authenticate the path; does not bind file bytes, SQLite WAL/SHM state, actor identity, consent or custody. Retained metadata must be held independently to detect coherent rollback. Never use this diagnostic alone for production Memory, privacy authority, a database transaction, file mutation, context release or Tool execution.

## Test and provenance evidence

Python 3.13.5 / pytest 9.0.2, local isolated exact source/test bytes:
**56 PASSED** (34 PNG inventory cases; 22 file-source pin cases), \`compileall\` PASS; all new source/test lines <=100 characters. Saved four Git Blob SHA values verified against local \`git hash-object\` after normal GitHub Contents API writes.

Extra read-only seeded checks (NOT committed as pytest): 2,500 PNG mutated payloads, with 28 admitted strictly as framing rather than decoded image evidence; 250 original-and-mutated source-pin pairs, with all expected stale metadata reviews rejected. No genuine camera photos, user records, decoded images or independent source/clock attestation.

GitHub Actions auto-triggered (no manual runs):
- PNG source #1382 / \`40372251312\` — QUEUED at observation.
- PNG tests #1383 / \`40372341887\` — QUEUED.
- Local file pin source #1384 / \`40372416840\` — QUEUED.
- Final source/test HEAD #1385 / \`40372604053\` — QUEUED.
- Earlier checkpoint #1381 / \`40364345469\` — QUEUED; Windows/Linux 3.11–3.13 jobs on that run queued.
- Historical #1244 / \`40237313817\` Ubuntu Python 3.13 pytest FAILED at \`tests/test_privacy_cross_process_veto_projection_run434.py:101\` (\`assert 1 == 2\`), a known old assertion adjusted in Run448; this does **not** establish latest-HEAD PASS. Its Windows pytest jobs remain IN PROGRESS; old runs predate the new 45-minute workflow timeout.

No whole-repository pytest/Ruff, Windows, Python 3.11/3.12, packaging/UI smoke or six-matrix GREEN obtained. Full clone is unavailable from the local container due to github.com DNS. No test results, SHA identities or reviews have been fabricated.

## Frozen boundaries and next plan

Frozen V1/V2/Local UI/Launcher evidence, Memory V1 Schema, ActionAudit V1, V3 Contract 1, provenance/contamination/regression/reproducibility gates and the protected final-evaluation boundary are **unchanged**. No paid/external compute, GPU, APIs, Candidate/weights, new secrets, physical hardware actions, real Memory/consent/deletion, real Tool execution, main merge, or automatic replay of UNKNOWN/RUNNING/reserved PENDING WRITE.

1. Naturally review exact-head CI; diagnose genuine source/test failures (including Windows), never rerun duplicate jobs or claim matrix GREEN from isolated tests.
2. Keep PNG inspection isolated until its exact-head and dependencies are GREEN; any image decoding, observation origin or consent integration requires independent provenance/privacy controls and bounded decompression.
3. Treat local file identity pins as diagnostic-only. A secure source handle, WAL-consistent DB snapshots, independently retained custody, and negative permissions are prerequisites to any real Memory/Planner/privacy database use.
4. Continue independent Memory CAS/event/expiry and Planner/ToolRegistry/PermissionGate/trusted-clock audit-before-action work without weakening frozen gates.
