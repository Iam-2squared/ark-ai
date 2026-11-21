# Run462 — Disconnected recurrence and SQLite schema boundaries

**Observed at:** 2026-10-26T21:55:09.314Z (wall clock; Asia/Tokyo 2026-10-27 06:55:09; NOT a trusted time source).
**Repository:** Iam-2squared/ark-ai
**Branch:** `research/jarvis-foundations`; PR #8 Draft/open/unmerged.
**Entry work-basis HEAD:** `a72c0b8b8fa078fe792921d57bdad5a133007ac1`
**Final source/test HEAD:** `9486ed2290d82169e2ed6bf6dbb048b8c89c63e9`
**This document's write-basis HEAD:** `9486ed2290d82169e2ed6bf6dbb048b8c89c63e9`. Its own resulting commit must be looked up separately.

## Package A: Synthetic recurring scheduler preview

- `src/ark/disconnected_schedule_preview.py` blob `861ca7357cf1331edd29414636430ac114b3b29c`.
- `tests/test_disconnected_schedule_preview_run462.py` blob `5ac7fd1600e31f3c00c6050b3009abccec20dad8`.
- Exactly typed, bounded interval recurrence (1–4096 occurrences, >=1000 ms period, at most 60 seconds grace); SHA-256-bound synthetic policy/index/due occurrence IDs and prior-cursor continuity.
- Four explicitly inert states: NOT_DUE, DUE_UNVERIFIED, EXPIRED_QUARANTINE, EXHAUSTED. A missed slot is never silently skipped or replayed. No clock lookup, dispatch, notification, consent, persistent cursor or actual scheduler integration.
- Local Python 3.13.5 isolated package pytest: **35 PASSED**. Additional seeded 3,000/3,000 consistent recurrence probes, including 1,586 late quarantine cases. These extra probes are NOT committed pytest fixtures.

## Package B: Read-only synthetic SQLite schema probe

- `src/ark/disconnected_sqlite_schema_probe.py` blob `cc76f000cd1bce50e73dda0e71bc9ada6fe1b711`.
- `tests/test_disconnected_sqlite_schema_probe_run462.py` blob `5760277b5247de75b47781f6ff9dcaad62e694dd`.
- Requires an already-open, exact, idle, query-only SQLite Connection with only `main` attached. Uses one transaction for repeated schema inventory; SHA-256 covers DDL-bearing `sqlite_master` entries, schema version and user version; bounded at 128 objects/65,536 encoded DDL bytes. No application rows are included in the returned seal. Rejects schema/index/view drift, invalid retained seals, write-enabled and attached connections.
- Local Python 3.13.5 isolated pytest: **11 PASSED**. Additional seeded 500/500 independent synthetic reviews: 120 stable and 380 intentionally drifted schemas rejected. These extra probes are NOT committed pytest fixtures.
- Limitations: this is not a source-authenticated DB inspection, a trusted external witness, an atomic multi-SQLite/WAL snapshot, complete row/event integrity, privacy erasure, or disclosure/execution authorization. Caller changes to connection config are outside this read-only probe's custody.

## Test integrity / CI

- Four saved source/test blob SHAs re-read from GitHub and matched local `git hash-object` at the test-reviewed byte level.
- Combined independent local pytest: **46 PASSED**; `compileall` PASS; AST accepted with Python 3.11 grammar. New code lines <=100 columns.
- One pre-save local test fixture used a slots dataclass `__dict__` incorrectly: corrected before the 46 PASS. One newly saved SQLite fixture f-string was then immediately fixed through the ordinary GitHub Contents update for Python 3.11 compatibility, and the final saved blob matches the re-tested local file. No safety bypass.
- This is **NOT** repository-wide pytest, Ruff, supported OS matrix, a complete assembled JARVIS, or six-matrix GitHub GREEN.
- Final source/test CI: **#1417 / 40408006256 QUEUED** at direct lookup, exact head `9486ed2290d82169e2ed6bf6dbb048b8c89c63e9`. Earlier package writes #1413–#1416 also QUEUED. No manual duplicate workflow dispatch.
- GitHub Actions branch-filtered snapshot: 166 QUEUED and 7 IN PROGRESS at inspection; old-head #1251 Windows jobs still in `Run pytest`. This is a material verification backlog, not evidence of latest-head failure or success. The later docs/checkpoint CI needs separate inspection.

## Frozen evidence and non-authorization

V1/V2/Local UI/Launcher, Memory v1 schema, ActionAudit v1, V3 Contract 1, provenance/contamination/reproducibility/regression controls, protected V2 final evaluation and main-merge approval remain untouched. PR #5 and #8 remain Draft/unmerged. No external/paid compute, Candidate adapter/weight creation/promotion, new credentials, real user data, real PC action, trusted-clock claim, irreversible operation, protected evaluation, or merge.

## Next plan

1. Investigate naturally advancing #1417 source-head CI, older failing Linux regression evidence and historical Windows pytest stalls without automatic reruns/cancellation or weakened tests.
2. Keep both new modules isolated until relevant lower-level exact-head GREEN; design an explicit durable cursor/occurrence witness and independently authenticated clock/consent boundary before any scheduler integration.
3. Continue Memory row/event/CAS/expiry and Planner UNKNOWN-WRITE quarantine on independent modules, then exact ToolRegistry/PermissionGate audit-before-action once prerequisites are validated.
