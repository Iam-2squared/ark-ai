# LATEST — ARK AI Run973: fix CI Ruff, proactive witness aliases, Memory CAS row hydration

**Saved at (Asia/Tokyo/JST): 2026-11-19T02:55:58.973+09:00** (reporting timestamp only; never a trusted audit/consent/expiry clock). **Overall JARVIS / ARK completion: NOT_PASSED.**

**Branch / PR:** `research/jarvis-foundations` / [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8), OPEN/DRAFT/UNMERGED at latest pre-write check. **Exact work-basis HEAD:** `573e6b70c48c7ae6fd3eb3c744aba6decdf3911f` (Run972 checkpoint). **Last executable source/test HEAD:** `9b529f81e6cb2cda1afa332a6e73d6709ad0ab44`. **Run973 report HEAD and checkpoint write-basis HEAD:** `62c53939c8c69d65cfb9c06c4718cb6ab66d978b`. **Checkpoint-result HEAD** is the returned normal GitHub Contents API commit SHA and live PR/branch SHA after the write; it cannot embed its own SHA in its committed text. This checkpoint captures only observed statuses, not a declaration of CI PASS.

**main:** `7a843f17eb96ed13d66f23b58b06406b3002e405` unchanged at latest pre-write check. Protected PR #5 `805b377697472268db02650a89c7a94b1c5337c8` and paused UI PR #9 `3b49048dd70eebcb6268299b9ecef4e301bbc0fd` both OPEN/DRAFT/UNMERGED/untouched.

## NEW this invocation — three coherent free-only non-UI packages, 11 authored tests

1. **Run972 CI failure repair:** [`d840a7c`](https://github.com/Iam-2squared/ark-ai/commit/d840a7cd94f4d62648d0d87ee9862283a62361d4) fixes Ruff I001 import sorting in the Run972 privacy recheck test with no test or authority relaxation. It follows the **six-job FAIL** of [CI #44352402823](https://github.com/Iam-2squared/ark-ai/actions/runs/44352402823) at `573e6b7` (Ruff stage). Older green runs do not cover that code.
2. **Proactive SQLite witness source path integrity:** [source `2565e35`](https://github.com/Iam-2squared/ark-ai/commit/2565e353c86069c450026fce33748f3ee522c640) + [tests `b493a81`](https://github.com/Iam-2squared/ark-ai/commit/b493a81cfb705ed23c23dbc3be8d824756a24f3b). Before read-only SQLite resolve/open, reject alias/hardlink/symlink targets using the existing original local path preflight; reject swapped preflight and executable Path subclass. **4 new authored tests**, not yet all-environment PASS certified. Path preflight remains TOCTOU, not atomic FD custody.
3. **Memory generation-fenced CAS row admission:** [source `5fe8d18`](https://github.com/Iam-2squared/ark-ai/commit/5fe8d18fc164f2f59f9358d1f7581b9e53e13242) + [tests `9b529f8`](https://github.com/Iam-2squared/ark-ai/commit/9b529f81e6cb2cda1afa332a6e73d6709ad0ab44). Reuse the existing Memory mutation SQL preflight before `SELECT *` in optional generation CAS snapshots. **7 authored regression cases** cover corrupted TEXT/BLOB/size plus normal Japanese identifier write. No Memory v1 schema/API change, no WRITE retry, no independent actor authorization.

[Run973 technical report](https://github.com/Iam-2squared/ark-ai/blob/62c53939c8c69d65cfb9c06c4718cb6ab66d978b/docs/JARVIS_RUN973_NON_UI_PROACTIVE_ALIAS_MEMORY_CAS_ROW_ADMISSION.md) · [Run972 exact checkpoint](https://github.com/Iam-2squared/ark-ai/blob/573e6b70c48c7ae6fd3eb3c744aba6decdf3911f/docs/PROJECT_STATUS.md) · [Unaltered archive through Run969](https://github.com/Iam-2squared/ark-ai/blob/3105cc40f542e930a0fd0ed622753ea226cd8e1b/docs/PROJECT_STATUS_ARCHIVE_THROUGH_RUN969.md).

## Tests / CI by exact commit, latest observation

- **Run972 exact checkpoint** `573e6b70c48c7ae6fd3eb3c744aba6decdf3911f`: [CI #44352402823](https://github.com/Iam-2squared/ark-ai/actions/runs/44352402823) **FAIL, 6/6 jobs**, Ruff I001. Cause repaired but subsequent CI not yet certified.
- **Ruff repair** commit `d840a7cd94f4d62648d0d87ee9862283a62361d4`: [CI #44362114514](https://github.com/Iam-2squared/ark-ai/actions/runs/44362114514) — **IN_PROGRESS** (as observed; not inheritable by newer HEAD).
- **Proactive alias source** commit `2565e353c86069c450026fce33748f3ee522c640`: [CI #44362633441](https://github.com/Iam-2squared/ark-ai/actions/runs/44362633441) — **IN_PROGRESS** (as observed; not inheritable by newer HEAD).
- **Proactive alias tests** commit `b493a81cfb705ed23c23dbc3be8d824756a24f3b`: [CI #44362771028](https://github.com/Iam-2squared/ark-ai/actions/runs/44362771028) — **IN_PROGRESS** (as observed; not inheritable by newer HEAD).
- **Memory prehydration source** commit `5fe8d18fc164f2f59f9358d1f7581b9e53e13242`: [CI #44363192338](https://github.com/Iam-2squared/ark-ai/actions/runs/44363192338) — **IN_PROGRESS** (as observed; not inheritable by newer HEAD).
- **Memory prehydration tests** commit `9b529f81e6cb2cda1afa332a6e73d6709ad0ab44`: [CI #44363321842](https://github.com/Iam-2squared/ark-ai/actions/runs/44363321842) — **QUEUED** (as observed; not inheritable by newer HEAD).
- **Technical report HEAD** `62c53939c8c69d65cfb9c06c4718cb6ab66d978b`: workflow may start automatically; at checkpoint observation no certified all-six verdict. Do NOT launch a duplicate manual run. This checkpoint write itself may trigger a fresh CI.
- No local physical PC/model tests were performed. CI jobs on earlier HEADs do **not** certify newer source/tests. Exactly-once WRITE, trusted clock/consent, cross-store atomicity, production integration and JARVIS completion remain NOT_PASSED.

## Frozen boundaries, authorization blockers

Frozen V1/V2/Local UI/Launcher evidence and controlling contracts, Memory v1, Observation Envelope v1, PlanStep/ToolCall v1, V3 protected final evaluation and contamination/provenance/reproducibility gates unchanged. PR #5 guarded Draft/unmerged, #8 Draft/unmerged, paused UI PR #9 untouched. No new frontend/source/tests, main merge, real tool dispatch, automatic uncertain WRITE retry, paid or external GPU, paid APIs, potentially billable service, Candidate adapter/weights/promotion, protected evaluation opening, credentials/secret/account connection, physical-PC action, destructive operation, consent forgery, or GitHub safety bypass. Independent approval, file-handle race protection, trustworthy runtime identity, model/hardware and real-world authority remain open gates.

## Next plan / 今後の方針

1. Establish **exact newest code/test/checkpoint HEAD** Windows/Ubuntu × Python 3.11–3.13 CI result. If FAIL, inspect specific job logs and apply smallest semantics-preserving normal-write fix. Avoid duplicate workflows and continue independent non-UI lanes while CI runs.
2. Expand Memory WAL/SHM and COMMIT-UNKNOWN crash safety, CAS/ABA and coherent row/event/expiry snapshots. No ambiguous retry or invented writer provenance.
3. Advance Planner terminal/restart recovery, immutable ToolRegistry, exact-type PermissionGate, durable one-shot approval and audit-before-action; integrate only on exact-head GREEN with disconnected/mock executor.
4. Continue private Personal Context revocation/reuse lifecycle, proactive occurrence/clock/replay fencing, Observation fixtures and free-only V3 path/provenance guards. **UI remains PAUSED**.

**ARK/JARVIS NOT_PASSED.**
