# ARK AI — Canonical Project Status

**LATEST — Run642 / 2026-11-06 JST: three non-UI core work packages saved, plus one Ruff import-spacing fix and a technical evidence report.** Read-only Memory COMMIT ambiguity now rejects replaced slotted result descriptors/attribute hooks before private SQLite access; new disconnected Planner same-step CAS/clock tests and cross-scope Memory reconciliation tests were added. **16 newly authored test cases (not yet verified as PASS).** A synthetic test import-spacing `I001` failure was repaired through the normal GitHub Contents API. Latest corrected six-job CI is **IN PROGRESS / NOT GREEN-CLAIMED**. UI stays paused; PR #5, #8, #9 Draft/unmerged. **ARK/JARVIS/V3 NOT_PASSED**.

**Saved at:** **2026-11-06T05:47:02.421+09:00 Asia/Tokyo/JST**, wall-clock sample immediately preceding the normal Contents checkpoint write; not authenticated audit time, human consent or execution authorization.

## LATEST — exact repository and work basis

- **Branch / PR:** `research/jarvis-foundations` / [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8), OPEN, unmerged.
- **Invocation work-basis HEAD:** `5d84f363b3e0405c96589313fd58d852f50aa5d6`; its [CI #42098379536](https://github.com/Iam-2squared/ark-ai/actions/runs/42098379536) is **6/6 GREEN**, Windows/Ubuntu × Python 3.11–3.13.
- **Checkpoint write-basis HEAD:** `227bb152f405d1fbb4d30943b5750b9bb39202fc`, freshly verified from PR #8 before this checkpoint. **Checkpoint-result HEAD:** assigned by GitHub *after* this write, not embedded falsely in its own content. Verify returned commit and live PR head separately.
- **A — Memory CAS outcome source:** `src/ark/memory/generation_cas_outcome_review.py` hardens exact original result field descriptors and `__new__` / `__getattribute__` / `__getattr__` hooks. Replaced executable carriers cannot be read before a preflight rejection. Commit `5871fdbc1d934008daba3f3b9bdba0d43613d173`. Nine new regression cases in `tests/test_memory_cas_outcome_preaccess_carriers_run642.py` (commit `38fe975916f999f75dc6350945576b21d7825cce`). No frozen Memory DDL change, no real dispatch.
- **B — Planner restart/race fixture:** `tests/test_planner_journal_same_step_race_run642.py`, commit `b2ba12c501b2b7dfbaa6542cffabd0e77b8fdffd`. Three cases check competing first RUNNING state transitions, single CAS winner, persisted recovered UNKNOWN/no replay, and timestamp/stale-revision denial.
- **C — Memory scope isolation:** `tests/test_memory_ambiguity_namespace_isolation_run642.py`, commit `97dfce64e8da586e724a49ca07cf3fef6c75299f`. Four cases check a distinct owner/namespace cannot be mistaken for the caller's COMMIT and identical target payload is not attribution.
- **Lint-only repair:** `I001` in the new Memory result test's import-block spacing corrected at `35b329ec58bf889bc23214fc1becfefe6711791b`. No runtime semantics relaxed.
- **Technical evidence:** [Run642 non-UI CAS outcome, Planner and Memory scope report](JARVIS_RUN642_NON_UI_CAS_OUTCOME_PLANNER_SCOPE_EVIDENCE.md), commit `227bb152f405d1fbb4d30943b5750b9bb39202fc`. **16 authored cases, not 16 confirmed pytest PASS.** Local clone failed on GitHub DNS; local Ruff/pytest not run.

## CI — observed evidence and unresolved verification

- Prior exact work-basis [#42098379536](https://github.com/Iam-2squared/ark-ai/actions/runs/42098379536): **6/6 GREEN**.
- Initial new test run [#42105615665](https://github.com/Iam-2squared/ark-ai/actions/runs/42105615665) and intervening [#42105732228](https://github.com/Iam-2squared/ark-ai/actions/runs/42105732228) / [#42105809871](https://github.com/Iam-2squared/ark-ai/actions/runs/42105809871): **6/6 FAIL at Ruff I001**, source untouched; read actual job logs. Fixed import spacing.
- Corrected test/source commit `35b329ec58bf889bc23214fc1becfefe6711791b`: [CI #42106130428](https://github.com/Iam-2squared/ark-ai/actions/runs/42106130428) **IN PROGRESS, six jobs** at last inspection.
- Report-only commit `227bb152f405d1fbb4d30943b5750b9bb39202fc`: [CI #42106283072](https://github.com/Iam-2squared/ark-ai/actions/runs/42106283072) **IN PROGRESS**. The checkpoint itself may trigger a new independent exact-HEAD workflow; do not claim GREEN prematurely or manually dispatch duplicate equivalent runs.

## Frozen controls, privacy, authority and blockers

- Verified `main` `7a843f17eb96ed13d66f23b58b06406b3002e405` unchanged; [Draft PR #5](https://github.com/Iam-2squared/ark-ai/pull/5) HEAD `805b377697472268db02650a89c7a94b1c5337c8`, [Draft PR #9](https://github.com/Iam-2squared/ark-ai/pull/9) HEAD `3b49048dd70eebcb6268299b9ecef4e301bbc0fd`, each unmerged. PR #9 untouched; all new UI/frontend work PAUSED; frozen V1/V2/Local UI/Launcher contracts, evidence and protected V2 final evaluation untouched.
- No paid/external GPU/compute/API, new subscription/account/credential, Candidate training/adapter/weights or promotion, physical-PC action, destructive persistent operation, real tool execution, camera/microphone access, or main merge. PR #5 remains Draft under explicit V3 approval gate.
- Synthetic SQLite journals, local hash witnesses, a caller-supplied clock and mock/READ-only diagnostic receipt are **not** trusted clock, audited consent, identity proof, cross-store atomicity, durable real-world exactly-once effects, or permission for automatic replay. Final hardware gate, V3 immutable identities, reviewer approvals and spend permission are unresolved.

## Next plan / 今後の方針

1. Confirm exact-head CI for the corrected source/tests on all six Windows/Linux jobs; if FAIL, use actual job logs, fix only the precise semantics-preserving issue via guarded Contents writes and immediately switch to another independent non-UI lane while CI runs.
2. Extend Memory generation/event row reconciliation and COMMIT-UNKNOWN manual triage under concurrent writers; Planner persisted UNKNOWN/FAILED/CANCELLED recovery with independent roots and crash boundaries.
3. Integrate ToolRegistry, exact PermissionGate, durable one-shot authorization, trusted-clock-audit-before-action and occurrence/replay fences in a **disconnected, mock-only** path after lower-level exact-head GREEN.
4. Work on privacy-safe Personal Context, proactive scheduler/readiness and offline observation fixtures; read-only V3 free authorization/path/identity guards. Keep frozen contracts and protected evaluation closed.
5. Historical checkpoints/evidence retained at [Run641 canonical status](https://github.com/Iam-2squared/ark-ai/blob/5d84f363b3e0405c96589313fd58d852f50aa5d6/docs/PROJECT_STATUS.md), [Run641 technical evidence](JARVIS_RUN641_NON_UI_MEMORY_RACE_SNAPSHOT_PLANNER_RETENTION.md), and the byte-verified [Run639 history part 1](status_archive/PROJECT_STATUS_THROUGH_RUN639_PART1.md) / [part 2](status_archive/PROJECT_STATUS_THROUGH_RUN639_PART2.md). This is the sole compact latest checkpoint for Run642.
