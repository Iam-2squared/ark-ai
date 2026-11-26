# Run974 — Non-UI bounded SQLite admission across Atomic / Memory / Proactive

**Work basis:** Run973 checkpoint and exact source HEAD `6b08f6171bb3e3eafc6bf40a88686900ec278040` on Draft PR #8, `research/jarvis-foundations`. This report is a reversible, free-only development record, **not** roadmap PASS evidence, a trusted provenance witness, or permission for external action.

## Package A — Atomic pre-action audit set bounded before hydration

- Source: [`91a1c56ea4b58a4a27e22635fc3ba5f09005132b`](https://github.com/Iam-2squared/ark-ai/commit/91a1c56ea4b58a4a27e22635fc3ba5f09005132b), `src/ark/agency/disconnected_atomic_preaction_ledger.py`, blob `54771fbd797398d687c6d32cabed4a79cfa0c5e1`.
- Tests: [`dbffb29fd0dc8203d97fa842ce76cc3c8e6733bf`](https://github.com/Iam-2squared/ark-ai/commit/dbffb29fd0dc8203d97fa842ce76cc3c8e6733bf), `tests/test_atomic_preaction_audit_cardinality_run974.py` (five authored tests, including three parametrized corrupt-audit variants).
- A bounded intent count no longer permits an arbitrarily large orphan audit set to reach byte/type sweep or row JOIN. Check audit cardinality immediately after the intent cardinality, prior to either table's private value scan. A clean paired history still reopens with all dispatch/auto-replay/independent-custody flags false.
- Local hash chains and matching pair counts are not an authenticated consent issuer or proof of external exactly-once effects.

## Package B — Memory expiry SQL admission covers whole due row

- Source: [`97b6fd5fca44f50bfb1a77e16e79c780a40e0d4d`](https://github.com/Iam-2squared/ark-ai/commit/97b6fd5fca44f50bfb1a77e16e79c780a40e0d4d), `src/ark/memory/sqlite_store.py`, blob `bb5897fb3097a18aaa084d75f38f1c143b910043`.
- Tests: [`607bb2297acf10fcedb775a701b3373fa456d93e`](https://github.com/Iam-2squared/ark-ai/commit/607bb2297acf10fcedb775a701b3373fa456d93e), `tests/test_memory_expiry_whole_row_admission_run974.py` (eight authored tests).
- The existing same-write-transaction due-page SQL preflight now rejects malformed persisted identity, scope, content hash, timestamps and revision, as well as content/source/metadata. It happens before `SELECT *` hydrates any due private row; an isolated good scope can still purge without reading a corrupted different-scope row.
- Memory v1 schema/API and legacy unlimited purge mode are unchanged. This is corruption admission, not trusted-time/independent actor custody or authorization to extend retention.

## Package C — Proactive history cap before per-row storage sweep

- Source: [`a2628fc9ad691556f432d6bf9ca7f82a6b0df85d`](https://github.com/Iam-2squared/ark-ai/commit/a2628fc9ad691556f432d6bf9ca7f82a6b0df85d), `src/ark/proactive_synthetic_review.py`, blob `236ccd69aa267e26e6df65f0dab6b9d72bcca8fc`.
- Tests: [`7db271bc26bbcaaee40a21face1700694e0cd976`](https://github.com/Iam-2squared/ark-ai/commit/7db271bc26bbcaaee40a21face1700694e0cd976), `tests/test_proactive_cardinality_before_sql_sweep_run974.py` (three authored tests).
- An independent `COUNT(*)` rejects excessive fixture rows before the existing aggregate per-row SQL integrity predicate, preserving exact canonical row checks under the bound.
- All preparation markers remain synthetic; no notification, capture, tool execution, trusted clock or auto-replay.

## Evidence status, exact HEAD

Previous Run973 checkpoint HEAD `6b08f6171bb3e3eafc6bf40a88686900ec278040`: [CI #44364128959](https://github.com/Iam-2squared/ark-ai/actions/runs/44364128959) **6/6 SUCCESS** (Ubuntu/Windows × Python 3.11/3.12/3.13).

New work: 3 production-source changes, 3 new standalone test files, **16 authored tests**. **Authored/saved is not all-platform PASS**. Latest observed exact-run CI:

| GitHub commit | CI ID | Latest observed state |
| --- | --- | --- |
| `91a1c56` Atomic source | [#44372876208](https://github.com/Iam-2squared/ark-ai/actions/runs/44372876208) | IN PROGRESS |
| `dbffb29` Atomic tests | [#44373033404](https://github.com/Iam-2squared/ark-ai/actions/runs/44373033404) | IN PROGRESS |
| `97b6fd5` Memory source | [#44373468314](https://github.com/Iam-2squared/ark-ai/actions/runs/44373468314) | IN PROGRESS |
| `607bb22` Memory tests | [#44373611059](https://github.com/Iam-2squared/ark-ai/actions/runs/44373611059) | IN PROGRESS |
| `a2628fc` Proactive source | [#44373722439](https://github.com/Iam-2squared/ark-ai/actions/runs/44373722439) | QUEUED |
| `7db271b` Proactive tests / latest executable source+test HEAD | [#44373857971](https://github.com/Iam-2squared/ark-ai/actions/runs/44373857971) | QUEUED |

No duplicate workflow dispatch. These are observations at report creation; rerun identifiers, final verdicts and physical model tests must not be invented.

## Gate protection / safe next work

PR #5 (V3 protected research) and PR #9 (paused UI) untouched, Draft/unmerged; PR #8 Draft/unmerged; main unchanged. V1/V2/Local UI/Launcher freezes, protected V2 evaluation and V3 Candidate contamination/provenance gates unchanged. No external paid service, GPU, protected evaluation, credentials, candidate weights/adapter/promotion, real hardware, live backend side effects, UI or main merge.

1. Establish exact HEAD CI; if FAIL, inspect job logs and make minimal semantics-preserving repair via normal GitHub file writes only, then switch lanes while CI runs.
2. Advance Memory WAL/SHM, cross-scope event completeness, CAS ABA, expired row and COMMIT-UNKNOWN recovery.
3. Advance Planner crash recovery / immutable ToolRegistry / PermissionGate / persistent one-shot authorization / audit-before-action, with detached mock-only tests and explicit non-authority.
4. Continue Personal Context privacy lifecycle, proactive replay/occurrence integrity, Observation fixtures and free-only V3 path/identity guards. Keep frontend paused.

**Overall ARK/JARVIS: NOT_PASSED.**
