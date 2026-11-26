# Run814 — One-snapshot Memory expiry and disconnected Planner/WRITE durable slot join

**Prepared:** 2026-11-12T17:54:27.100+09:00 (observed JST; NOT a trusted action clock).
**Branch:** `research/jarvis-foundations` / [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8), open/unmerged. Initial work-basis HEAD `a05f71f90d750aa593013d90902286f47dbfdd76`.

## New package A: coherent multi-scope expiry diagnostics

- `src/ark/memory/coherent_expiry_snapshot_review.py` committed `cdd3209440c480acc397757e26235ee8edee59aa`.
- `tests/test_coherent_expiry_snapshot_run814.py` committed `840b7ffafb1199a7ab624fd4ad311a1baa1ccece`, amended for an unused-import-only Ruff F401 fix at `2c954e4796d14b40ef25b1ec8637d08ed3dff458` (test file blob `87a83e3f34edfb0d726c5391750d50fa62c35277`).
- **19 new regression cases submitted**, including quiescent equality to the original bounded single-scope expiry previews, a concurrent WAL writer between two scope reads, `limit+1` truncation, strict owner/scope/time/budget types, forged verifier/authority descriptors, malformed event lifecycle and scope retargeting.
- Implementation reads all requested due pages from **one** `SQLiteMemoryStore._connect_readonly()` handle and **one `BEGIN` read transaction**, with one caller-supplied clock value, 1–16 exact same-owner scopes, 100 rows per scope plus overflow and shared 40,000-event validation cap. Validates Memory v1 DDL, global event count and candidate event histories, and hashes only content-free candidate identity/revision/metadata digests into existing `MemoryExpiryPreview`/`MemoryExpiryCohort` structures.
- This read is NOT a deletion command, authenticated consent/clock, independent source custody, real-time freshness after return, or atomic snapshot of other SQLite stores. Local coherent Memory epochs can still become stale immediately after transaction closure. It does not touch the existing public Memory store API.

## New package B: durable WRITE slot ↔ recovered Planner hold receipt

- `src/ark/agency/disconnected_planner_slot_restart_bridge.py` added at `2c22f138851708eae2de686bb85bc39788667991`, strengthened cross-source reservation/plan-state agreement at `ed54ff0cee08c710d888f86d8e1680773401b811`.
- `tests/test_disconnected_planner_slot_restart_bridge_run814.py` committed `bc5433a9d1b5faaf6c149ce3392a3e013659c379` — **18 new regression cases submitted** including one persisted SQLite reservation read after reopening, full-step state/dependency/WRITE inventory mismatch, missing/stale/forged slots, false observations, reentrant verifier replacement, and an interrupted RUNNING WRITE rendered UNKNOWN without granting replay.
- Joins the existing verified `review_disconnected_restart_receipt_bundle()` from Planner journal+dependency evidence to the existing read-only persisted-slot `review_disconnected_write_restart()` with a caller-retained `WriteSlotLedgerWitness`. A strict <=24-step synthetic DAG is required because the slot reviewer has its own 24-step bound. Every step remains held; no actual `ToolBackend`, clock, permission token or OS/network action is invoked.
- Different stores are read **sequentially**, not transactionally. Independently expected WRITE membership remains caller-supplied. A consistent local digest is not independent provenance, a consent record, audit-before-action proof, external exactly-once proof, a release from UNKNOWN or authorization to replay.

## Verified CI and limitations at report preparation

- **Previous exact Run813 checkpoint** `a05f71f90d750aa593013d90902286f47dbfdd76`: [CI #43179600522](https://github.com/Iam-2squared/ark-ai/actions/runs/43179600522) **GREEN 6/6**; six Windows/Ubuntu Python 3.11–3.13 jobs individually inspected.
- First new test+source CI [#43185478293](https://github.com/Iam-2squared/ark-ai/actions/runs/43185478293) **FAIL 6/6**; later combined-package [#43185974960](https://github.com/Iam-2squared/ark-ai/actions/runs/43185974960) **FAIL 6/6**, both due the same verifiable Ruff F401 unused import in the Memory test (`dataclasses.replace`). No execution semantics or assertions were weakened; the unused import was removed.
- Fixed commit `2c954e4796d14b40ef25b1ec8637d08ed3dff458` triggers [CI #43186098223](https://github.com/Iam-2squared/ark-ai/actions/runs/43186098223); **IN PROGRESS** at the last read during report preparation. The 37 newly submitted tests are **not** claimed locally run or exact-latest-HEAD GREEN. Later report/checkpoint writes will produce a different HEAD requiring independent exact-HEAD CI evidence.
- Historical cross-process Personal Context revocation issue was inspected read-only: previously logged loser-error string was not retained; root cause **UNDETERMINED**. No speculative fix or loss of privacy veto was introduced.

## Frozen gates / spend

All work is free-only, local/disconnected, non-UI, isolated on Draft PR #8. Protected V1/V2/Local UI/Launcher evidence and the V2 final evaluation were not opened or changed. Protected [PR #5](https://github.com/Iam-2squared/ark-ai/pull/5) and paused UI [PR #9](https://github.com/Iam-2squared/ark-ai/pull/9) remain Draft/unmerged and untouched. No paid/external GPU, APIs, training, Candidate weight creation/promotion, credentials, real side effects, Memory purge, or main merge. JARVIS remains NOT_PASSED.

## Next

1. Confirm the corrected exact-head six CI jobs, inspect actual failures and fix only the corresponding cause if any; overlap with an independent lane rather than polling.
2. Establish independently retained WRITE inventory and post-crash UNKNOWN terminal reconciliation without transforming local SHA receipts into real authority.
3. Continue Memory CAS/ABA and COMMIT-UNKNOWN manual reconciliation, exact-clock/privacy lifecycle and cross-process fixtures; real action backend remains disconnected.
4. Continue ToolRegistry/PermissionGate one-shot audit-before-action, proactive scheduler/observation, free V3 guards; preserve UI pause and all frozen boundaries.
