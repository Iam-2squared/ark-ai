# ARK Run627 — Non-UI validator custody, global expiry high-water, and READ recovery

**Status:** Implementation and 19 new parameter-expanded pytest cases **AUTHORED** on Draft PR #8. This is **not** a claim of local pytest PASS, final exact-head CI GREEN, writer authentication, trusted clock, or JARVIS completion.

## Work basis and boundaries

- Starting exact-head / previous canonical checkpoint: `20ea76f0441696c00fb75d06ad37019d35c4046b` (Run626).
- Branch: `research/jarvis-foundations`, Draft PR #8 (unmerged). Source/test work HEAD before this document: `2435c886cc8d135d56f663c60d8cf30bc1439705`; 8 ordinary guarded GitHub Contents commits / 8 changed files.
- Baseline [CI #41984293999](https://github.com/Iam-2squared/ark-ai/actions/runs/41984293999) completed Ubuntu/Windows × Python 3.11–3.13 **6/6 GREEN** on starting HEAD.
- Local GitHub DNS `git ls-remote` failed: `Could not resolve host: github.com`. **No local pytest, Ruff, real-PC GGUF, GPU, or external action executed.**
- New source/test CI is pending and must be judged on its **exact** commit HEAD. Tests are counted as authored cases, not passed tests.

## Package A — Snapshot request validator custody

- Source: `src/ark/memory/coherent_snapshot_review.py`, commit `f0e1fcba3bc0916510c09520e7fc525d010e6536`.
- Test: `tests/test_memory_snapshot_request_validator_custody_run627.py`, commit `34e2e8d4a33efa2e0dbcd216f3e6cf59a937ff8c`, **3 cases**.
- The opt-in snapshot reconstructs an existing `CoherentSnapshotRequest` to validate values. Dataclass `__init__` and `__post_init__` are executable, so the reviewer now checks original import-time identities before invoking them and refuses substituted constructors. The detached snapshot/result type and digest format are unchanged.

## Package B — PermissionGate exact grant validator

- Source: `src/ark/agency/policy.py`, commit `940c1fda064909b3e8832dba4c203971735670fe`.
- Test: `tests/test_permission_grant_original_validator_run627.py`, commit `2fb4a4b51d4d704f1c697d9157e6cb4109fd688f`, **6 cases**.
- The gate previously reconstructed a `CapabilityGrant` for validation without pinning its dataclass initializer and post-init implementation. Capture both originals at module load and reject substitutions before constructing. Cover READ and process-local WRITE authorization, hostile constructors that must not run, unchanged valid grants, and no consumed WRITE token on rejection. **No actual ToolBackend dispatch or durable approval is implied.**

## Package C — Memory expiry across the global append high-water

- Source: `src/ark/memory/expiry_candidate_preview.py`, commit `afc8b7177c3c9200fbc01428643e24c7a455f386`.
- Test: `tests/test_memory_expiry_global_event_highwater_run627.py`, commit `a6da7b3b876d607baaae23dc9fbd2c804452aa7d`, **6 cases**.
- A candidate's own history may be intact while an event for another owner or a previously deleted row is gone. The read-only expiry preview now verifies global `memory_events` count, contiguous IDs, and `sqlite_sequence` high-water **inside the same SQLite read snapshot**, including empty due pages. Per-candidate lifecycle checking remains first, retaining existing error semantics for missing selected-row events. The preview still cannot delete, consent, authenticate historical writers, or establish physical erasure.

## Package D — Detached READ recovery constructor custody

- Source: `src/ark/agency/disconnected_read_recovery_schedule.py`, commit `685e329293e8aaef22b913797c90c7883cfa1bcf`.
- Test: `tests/test_detached_read_recovery_constructor_custody_run627.py`, commit `2435c886cc8d135d56f663c60d8cf30bc1439705`, **4 cases**.
- A forged `ReadRecoveryDecision.__init__` or `DetachedReadRecoverySchedule.__init__` could execute before an inert-result assertion. Cache original initializer identities and recheck immediately before construction, including after hash callbacks. Recovered states remain untrusted; `READY_MOCK_ONLY` is not dispatch authority and ambiguous READ/WRITE outcomes cannot be auto-replayed.

## CI evidence and review status

- **Starting predecessor:** run #41984293999, GREEN 6/6.
- **Run627 intermediate:** [#41990247850](https://github.com/Iam-2squared/ark-ai/actions/runs/41990247850) for policy+snapshot test head; results require refresh at exact HEAD.
- **Run627 Memory expiry test head:** [#41990564187](https://github.com/Iam-2squared/ark-ai/actions/runs/41990564187); results require refresh.
- **Run627 final source/test:** [#41990999173](https://github.com/Iam-2squared/ark-ai/actions/runs/41990999173); may be queued/in progress. A later report/checkpoint commit triggers its own CI; do **not** treat earlier-head success as final checkpoint GREEN.
- User-facing checkpoint `docs/PROJECT_STATUS.md` is updated **once near invocation end**, only after meaningful source/test work and fresh HEAD check.

## Frozen scope and forward plan

PR #5 remains Draft/unmerged under real V3 identity, license/provenance, human dataset review and user approval/spend gates. PR #9 is Draft/unmerged with **all new UI/frontend work paused**. Main, frozen V1/V2/Local UI/Launcher evidence and Contract 1 remain unchanged. No paid or potentially billable compute, real Candidate generation, credentials/account links, physical PC actions, protected V2 final evaluation, real tool execution, auto-promotion, destructive operations, or approval-required merge.

**Next:** verify exact-head Ubuntu+Windows six-job CI; fix only failures grounded in logs, then strengthen Memory CAS/COMMIT-UNKNOWN reconciliation, Planner durable recovery, registry-bound PermissionGate and audit-before-*mock*-action. All local SQLite/SHA receipts are diagnostic, not consent, trusted time, authenticated provenance or external exactly-once.
