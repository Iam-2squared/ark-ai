# LATEST — ARK AI Run970: three disconnected recovery vector fixes, complete status-history archive

**Saved at (Asia/Tokyo/JST): 2026-11-18T23:51:01+09:00** (reporting time only, **not** a trusted consent, audit, occurrence, or expiry clock). **Overall ARK/JARVIS: NOT_PASSED.**

**Branch / PR:** `research/jarvis-foundations` / [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8), OPEN/DRAFT/UNMERGED at preflight. **Exact work-basis HEAD:** `362f14cd0bd23848788a5e5db6001cf44239ee35` (Run969 checkpoint). **Last new source/test HEAD:** `e2b251201a68c52c44feadd4a7439a4949c5d1d4`. **Run970 technical-report HEAD:** `e225054b093a7b401296cfa087d56d55f0190ab2`. **Preserved complete Run969-and-earlier status-history archive HEAD / checkpoint-write basis:** `3105cc40f542e930a0fd0ed622753ea226cd8e1b`. **Checkpoint-result HEAD cannot be literally embedded in its own contents commit:** use the normal Contents API returned commit SHA and live PR/branch HEAD after the write. **main:** `7a843f17eb96ed13d66f23b58b06406b3002e405` unchanged at preflight. Protected PR #5 Draft `805b377697472268db02650a89c7a94b1c5337c8`; paused UI PR #9 Draft `3b49048dd70eebcb6268299b9ecef4e301bbc0fd` unchanged.

## NEW in this invocation — saved implementation and tests, not yet certified on newest exact HEAD

1. **Memory expiry-restart review:** `dc520aa7` pins its complete receipt descriptor guard-field vector before processing pages, hashes, or a retained witness. `7a12ac28` adds **4** negative vector-mutation tests (empty, truncation, reversed, rebuilt tuple). Memory v1 and automatic purge restrictions unchanged.
2. **Atomic audit COMMIT-UNKNOWN:** `212c6735` protects both result-field and ledger-hook guard vectors before any SQLite or claim access. `78f42c3e` adds **8** negative and **1** positive inert genesis/no-replay cases. No externally authenticated effect, automatic replay, or dispatch.
3. **Planner/WRITE-slot restart:** `28a3d0f7` pins result/class/field/hook input guard vectors before either disconnected child reviewer. `e2b25120` adds **12** negative mutation cases. No automatic WRITE retry, shared cross-store atomicity claim, or execution.
4. **Evidence and checkpoint hygiene:** [Run970 technical report](https://github.com/Iam-2squared/ark-ai/blob/e225054b093a7b401296cfa087d56d55f0190ab2/docs/JARVIS_RUN970_NON_UI_RESTART_VECTOR_CUSTODY.md). The preceding **1,043,199-character** canonical status history was preserved **byte-for-byte** as [PROJECT_STATUS_ARCHIVE_THROUGH_RUN969.md](https://github.com/Iam-2squared/ark-ai/blob/3105cc40f542e930a0fd0ed622753ea226cd8e1b/docs/PROJECT_STATUS_ARCHIVE_THROUGH_RUN969.md). Archive blob SHA `f3fc02bb663b813157350bcc0498925ef10f6db8` **equals the original Run969 canonical status blob**. This short LATEST file is now the sole live checkpoint; prior full status evidence is linked, not discarded.

**25 new authored tests** across three safe independent non-UI packages. No deletion or weakening of assertions. No complete local pytest/Ruff or physical-PC verification.

## CI — commit-specific, as observed

- Work-basis `362f14cd...` [#44320183286](https://github.com/Iam-2squared/ark-ai/actions/runs/44320183286): **GREEN / SUCCESS, all six Windows+Ubuntu × Python 3.11–3.13 jobs**. This does **not** certify Run970.
- Previous Run969 report `125c2fb...` [#44319736792](https://github.com/Iam-2squared/ark-ai/actions/runs/44319736792): **SUCCESS**.
- Run970 Memory source [#44327352892](https://github.com/Iam-2squared/ark-ai/actions/runs/44327352892), Atomic source [#44327482717](https://github.com/Iam-2squared/ark-ai/actions/runs/44327482717), Memory test [#44327646057](https://github.com/Iam-2squared/ark-ai/actions/runs/44327646057): **IN PROGRESS** at last sample.
- Atomic test [#44327726610](https://github.com/Iam-2squared/ark-ai/actions/runs/44327726610), Planner source [#44328037759](https://github.com/Iam-2squared/ark-ai/actions/runs/44328037759), Planner test [#44328099797](https://github.com/Iam-2squared/ark-ai/actions/runs/44328099797), report [#44328473955](https://github.com/Iam-2squared/ark-ai/actions/runs/44328473955), archive [#44328552811](https://github.com/Iam-2squared/ark-ai/actions/runs/44328552811): **QUEUED** at last sample. This checkpoint may auto-start an additional CI run. **Latest exact checkpoint all-six GREEN not established.** No duplicate workflow runs were launched.

## Frozen / restricted boundaries

Frozen V1/V2, Local UI, Launcher, Memory v1, Observation Envelope v1, V3 Contract 1, final-evaluation gate, provenance/contamination/regression/reproducibility contracts unchanged. PR #5 protected Draft/unmerged; PR #9 UI paused Draft/unmerged/untouched; PR #8 Draft/unmerged; main unmodified. No paid or potentially billable service, external GPU/compute, Candidate generation/promotion, protected evaluation, new secrets/connections, physical PC, irreversible mutation, real tool dispatch, unauthorized merge, bypass or force push. Local hashes and diagnostics do not prove consent, trusted time or external exactly-once effects.

## Next plan / 今後の方針

1. Verify exact Run970 code/test/checkpoint CI all **6 jobs**. On failure inspect traceback, fix minimally by normal Contents writes and work in other independent non-UI modules while CI runs.
2. Advance Memory WAL/SHM, CAS/ABA, row/event/expiry coherent snapshot recovery and manual-only COMMIT-UNKNOWN triage; keep Memory v1 frozen.
3. Improve Planner terminal/crash recovery, immutable ToolRegistry/PermissionGate and audit-before-action via disconnected mock stages with exact-head GREEN evidence.
4. Continue privacy-safe Personal Context, Proactive Scheduler occurrence/replay/clock fences, Observation fixtures and free V3 path/approval/identity guards. **UI development remains PAUSED.**

**ARK / JARVIS NOT_PASSED.**
