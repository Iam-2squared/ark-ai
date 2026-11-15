# ARK AI Run897 — non-UI synthetic privacy WAL classifier and Planner journal ingress

**Observed report time (ordinary clock, UTC):** 2026-11-15T13:55:35.149Z. Not a trusted execution clock, consent, independent custody or proof of permissions. **JARVIS overall: NOT_PASSED.**

**Work basis:** `2d195182e0f14e3af83f7e11dbcffc02bb66f307` (Run896 checkpoint). Work performed exclusively on `research/jarvis-foundations` / [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8). Paused UI PR #9, protected learning PR #5, frozen V1/V2/Local UI/Launcher contracts and main were not changed.

## Package A — bounded WAL loser/winner diagnostics

- Source: [`97dadef6`](https://github.com/Iam-2squared/ark-ai/commit/97dadef6fea3deba34b3c847a97c0c07ecf05e75) modifies only `scripts/diagnose_revocation_wal_processes.py`.
- Tests: [`480fe428`](https://github.com/Iam-2squared/ark-ai/commit/480fe4289bafa6e19a20c93eae906e0623bde81f) adds five authored cases in `tests/test_revocation_wal_ambiguous_patterns_run897.py`.
- A genuine synthetic veto row may be independently readable even if the losing child refuses at bootstrap or after release. This now reports `durable_ambiguous_phase_patterns` separately from `unverified_phase_patterns`, using ONLY fixed child phase/status labels. It does not disclose raw stderr, exception text, database paths, personal scopes or private data.
- The two aggregates cannot prove winning writer identity, authenticated/independent provenance or an unbroken filesystem handle. A successful child reply without durable readback remains **anomaly/FAIL**; durable readback with one refused child also remains **anomaly/FAIL**. Anomaly return code and immutable no-retry/no-safety-relaxation flags are preserved.
- Still unresolved: Windows SQLite WAL/SHM last-close/disappearing-path race and open-handle alias custody; this diagnostic does **not** make a loser safe to retry.

## Package B — Planner journal fail-fast admission

- Source: [`ecae864a`](https://github.com/Iam-2squared/ark-ai/commit/ecae864a0e6149d8ee5a3dcb773a8f73d12729ea) changes only `src/ark/agency/planner_journal_review.py`.
- Tests: [`8304b7b7`](https://github.com/Iam-2squared/ark-ai/commit/8304b7b7bbde7ee38ac1dfc716870fd9144dbbf2) and expectation-only correction [`fde56a5d`](https://github.com/Iam-2squared/ark-ai/commit/fde56a5d098959f6604c001cb0f13ae1d9078324) add five authored cases in `tests/test_planner_journal_id_preflight_run897.py`.
- `SyntheticPlanJournal.append` now applies the already-established `PlanGraph` 4,096-byte UTF-8 identifier admission to the direct caller's step ID before inspecting the retained plan or touching SQLite. Exact foreign objects, over-budget ASCII/multibyte identifiers, and lone surrogates fail closed as `SyntheticPlanJournalRejected`. There is no frozen dataclass/schema change.
- One positive synthetic READ step is journaled as RUNNING and recovered cold as **ambiguous**, not an automatic replay or dispatch authorization. The tests exercise normal behavior and a failure-before-plan-iteration/SQLite sentinel. No live ToolBackend is called.
- The expectation-only correction changes `"RUNNING"` to the actual frozen `StepState.RUNNING.value == "running"`. This does not alter production behavior.

## Evidence and explicit limits

Starting [CI #43716659129](https://github.com/Iam-2squared/ark-ai/actions/runs/43716659129) at the exact work-basis HEAD is **GREEN 6/6** (Windows/Ubuntu × Python 3.11–3.13). This previous GREEN is **not** transferred to new commits. New CI runs began automatically on pushed PR commits, without manual duplicate dispatch:

- [#43721045251](https://github.com/Iam-2squared/ark-ai/actions/runs/43721045251) — WAL diagnostic source `97dadef6`; in progress at first observation.
- [#43721117479](https://github.com/Iam-2squared/ark-ai/actions/runs/43721117479) — five WAL tests `480fe428`; in progress at first observation.
- [#43721246269](https://github.com/Iam-2squared/ark-ai/actions/runs/43721246269) — Planner journal source `ecae864a`; in progress at first observation.
- [#43721303865](https://github.com/Iam-2squared/ark-ai/actions/runs/43721303865) — initial five Planner tests `8304b7b7`; queued at first observation (contains the subsequently corrected uppercase expected state).
- [#43721341913](https://github.com/Iam-2squared/ark-ai/actions/runs/43721341913) — corrected complete source/test `fde56a5d`; queued at first observation.

**Ten new regression cases are authored, not yet certified exact-head six-job GREEN at report creation.** All Python source/test modifications were made through the normal GitHub Contents API with a fresh PR HEAD recheck before each write; no raw object/ref bypass. The documentation and eventual canonical status checkpoint also use the normal path.

## Continuation and dependencies

1. Verify latest complete-head CI jobs and resolve any failures without weakening fail-closed semantics. Cross-lane work can proceed while CI runs; do not issue duplicate equivalent workflows.
2. Use classified synthetic winner/loser outcomes to narrow Windows WAL/SHM last-close behavior, without trusting a path-only or child-reported success.
3. Advance Planner COMMIT-UNKNOWN recovery, Memory CAS/expiry and snapshot integrity, immutable registry-bound permission checks, durable audit-before-action and disconnected Mock READ integration **only after exact relevant GREEN**.
4. Keep Personal Context privacy/retention, proactive scheduling, observation fixture contracts, and disconnected free-only V3 approval/path/identity guards on separate reversible lanes.
5. No new UI/frontend work, paid/external compute/GPU/API, physical PC action, real Candidate/training/promotion, final V2 opening, private ingestion, real WRITE, main merge or irreversible operation. No authorization was inferred from a synthetic hash, timestamp, readback or test result.
