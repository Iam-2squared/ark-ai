# JARVIS Run443 — detached READ-tool batch and local lexical Context search

These are two isolated, reversible Python 3.11-compatible modules operating on **caller-supplied synthetic data only**. Nothing here authenticates human approval, verifies trusted time, invokes a live ToolBackend, loads private Memory or enables file/network/OS actions.

## Package A — detached bounded READ-tool batch plan

Source: src/ark/agency/disconnected_batch_plan.py (Git blob df72ad0f4d86d6346d2c70beb7ff18d98c0d1f43).
Tests: tests/test_disconnected_batch_plan_run443.py (Git blob 6d1b68834804a1c023aee7565387a4e3a8c09224).
**26 locally PASS** with Python 3.13.5.

The local plan can describe up to 24 ordered steps restricted to math.sum, text.stats, text.find and json.inspect. It binds exact request and step IDs, canonical JSON input, sorted earlier-step-only dependencies and ordered membership in a domain-separated SHA-256. It rejects duplicate keys, floats/nonfinite values, integer overflow, invalid Unicode, unsafe operations, forward/self references, duplicate steps, excess depth and oversized arguments. A separate retained digest can expose local artifact drift, but both digest and artifact can be forged by a party that controls both. This does not import or integrate the still-unverified Run442 disconnected executor, ToolRegistry or PermissionGate. Dispatch, WRITE, replay and external execution evidence remain **False**.

## Package B — deterministic on-device lexical Context fixture search

Source: src/ark/offline_context_search.py (Git blob c8f923e7fe032c7ff2ed82d4c694d7fcafc0554c).
Tests: tests/test_offline_context_search_run443.py (Git blob d1ebb1a53cd4959aea0cbb5547c594efb30214f5).
**37 locally PASS** with Python 3.13.5.

The search accepts up to 32 synthetic owner/scope records sorted by unique ID, each with bounded UTF-8, a checked SHA-256 and a future expiration relative to *untrusted caller time*. A contaminated, foreign-scope, stale, corrupted or oversized record vetoes the whole batch. The output is a deterministic bounded selection of at most eight local matching excerpts; it is **not** real user Memory, model inference, verified consent, privacy approval or export permission. Search snippets may contain private caller text; do not log or export them. Consent, external export, tool dispatch and retention permissions remain **False**.

## Exact saved basis, test and CI scope

- Run442 checkpoint work-basis HEAD: 60eab2ba7aeb85079244aad780b3e92e8d74b57d.
- Final two-package source/test HEAD: a0f700e2c13b111d823f46b52639f71e14660621.
- GitHub compare: 4 commits, 4 new files, no modification/deletion of pre-existing files. All 4 GitHub blob SHAs matched the exact bytes used by local Python tests.
- Local Python 3.13.5 isolated PYTHONPATH pytest: **63 passed** (26 + 37); Python compileall PASS; no new line exceeds 100 characters. The test fixture builder for a lone surrogate originally raised an encoding error before reaching the tested module; fixed locally before uploading any second-package files.
- **No full-repository pytest, Ruff, Windows/Python 3.11–3.13 or packaged-app GREEN**. Full repository checkout from the container failed DNS, and Ruff was not installed. This is not a declaration of integrated capability.
- Final source HEAD CI #1286 / run ID 40271622461 was **QUEUED**, all six jobs queued. Opening Run442 checkpoint CI #1282 / 40266617246 was also **QUEUED**. An independent CI snapshot showed 51 queued, 7 in progress, with older Run433 checkpoint #1231 3/3 Ubuntu GREEN but 3/3 Windows pytest in progress. The old Windows huge pytest-name issue is not yet confirmed resolved by exact-head GREEN. No duplicate CI dispatch, rerun or cancellation.

## Next plan / 今後の方針

1. Inspect exact source, document and checkpoint CI across Ubuntu/Windows 3.11–3.13; fix actual failures via normal GitHub Contents only after rechecking current HEAD.
2. Only after both Run442 disconnected executor and this detached batch have their required GREEN evidence, connect them in an isolated **mock-only** fixture execution flow. Never infer authorization, external receipt or automatic retry from matching local SHA-256.
3. Only after Context, revocation and local search reach their own GREEN, design explicit local privacy admission with fresh revocation veto before using actual Memory. Search does not establish consent.
4. Continue separate Memory CAS/expiry/row-event integrity and crash/reopen recovery work when their lower-level exact-head CI gates permit. Unknown, running and reserved pending WRITE must never replay automatically.
5. Keep frozen V1/V2/Local UI/Launcher, Memory V1, ActionAudit V1, V3 Contract 1, PR #5 Draft/unmerged/NOT_PASSED, PR #8 Draft/unmerged. No spending, external GPU, Candidate generation, protected evaluation opening, promotion, irreversible action, new credentials, physical-PC action or main merge.

**Complete JARVIS: NOT_PASSED.** This document records bounded, disconnected, non-authoritative groundwork only.
