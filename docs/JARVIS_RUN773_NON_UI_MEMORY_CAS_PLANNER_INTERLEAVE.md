# ARK AI Run773 — Memory WAL startup race and disconnected Planner cross-store interleavings

**Date:** 2026-11-11 JST. **Work basis:** Draft PR #8 `research/jarvis-foundations`, `56a45db5b21f8547efdeb912cf49ec2e9fdba826` (Run772 checkpoint). **Scope:** fully free-only, non-UI, disposable local SQLite and mock-only test evidence. All real WRITEs, tools, notifications, paid compute, Candidate generation, protected evaluations and main merges remain blocked.

## A. Run772 CI diagnostic and a narrow Memory test-harness repair

- CI [#42880906530](https://github.com/Iam-2squared/ark-ai/actions/runs/42880906530) for previous Run772 report HEAD had an actual **Ubuntu Python 3.13 failure**, not a proved regression in production CAS: `tests/test_memory_multiprocess_generation_cas_run771.py::test_independent_processes_race_one_generation_token[True]` got **[0,1]** instead of **[0,4]**. The child traceback was `MemorySchemaError: memory SQLite sidecar path is not a single regular file` while constructing `SQLiteMemoryStore`; the other child completed. That test concurrently bootstrapped separate SQLite connections, which can race normal WAL sidecar teardown and the intentionally fail-closed pathname preflight. The error was **not** an unauthorized second update or a false CAS success.
- Ordinary Contents commit `381a19d3401d8debb64d90fc5e08cb43c5a80915` updates only `tests/test_memory_multiprocess_generation_cas_run771.py`: a parent-held local WAL connection keeps sidecars alive, each independent child **finishes initialization before the next child starts**, both signal readiness and then race the same CAS token behind one gate; all child stderr and exit assertions remain checked. This isolates the intended CAS contention from a distinct initialization/sidecar lifecycle race.
- **No production path guard, schema rule, CAS semantics or permission was loosened.** This does not certify filesystem TOCTOU safety or guaranteed external exactly-once actions. The earlier Run772 Run425 startup failure remains independently unconfirmed; this change does not claim to repair that unrelated test. Full Windows/Ubuntu CI for the new test HEAD is **not claimed GREEN** here.

## B. Independent SQLite state interleavings stay manual-only

- Ordinary Contents commit `43bde66aaf77d37855270d1e53939995c2f562c1` adds `tests/test_registered_planner_cross_store_interleave_run773.py`: **three** standalone synthetic cases, using registered WRITE/READ calls and a backend that raises if invoked.
- Case 1: **both** WRITE occurrence identities have valid local pre-action audit chain matches while Planner has a recovered **RUNNING** WRITE and dependent READ; outputs stay `QUARANTINE_WRITE_UNKNOWN`, `HOLD_UNCERTAIN`, `HELD_WRITE_APPROVAL` and all authority/proof flags remain false.
- Case 2: append a second atomic reservation **after** capturing the retained witness, then ask for the obsolete witness: entire cross-store review must reject, not mix versions.
- Case 3: append a Planner terminal `FAILED` event **after** capturing a prior RUNNING recovery object, then review the retained prior image: it is still only a manual UNKNOWN classification; detached local evidence never gains permission or a simultaneous cross-store snapshot claim.
- **Boundary:** Planner and pre-action audit stores have separate SQLite transactions and untrusted local custody. Even two `LOCAL_MATCH` values do not establish human consent, authenticated actor, independent provenance, a genuine external write, or permission to replay an ambiguous effect.

## Exact SHA/CI evidence

- Run772 checkpoint initial HEAD `56a45db5b21f8547efdeb912cf49ec2e9fdba826`. Its [CI #42881782256](https://github.com/Iam-2squared/ark-ai/actions/runs/42881782256) was **IN_PROGRESS** at first check; at that sample Ubuntu 3/3 GREEN, Windows in progress. Earlier [CI #42880906530](https://github.com/Iam-2squared/ark-ai/actions/runs/42880906530) had Ubuntu 3.13 FAIL with the captured child-sidecar traceback; do not extrapolate.
- New Memory test HEAD `381a19d3401d8debb64d90fc5e08cb43c5a80915`: no matching PR-triggered workflow was returned by the connector at first search (no independent PASS claimed).
- New Planner test + Memory fix HEAD `43bde66aaf77d37855270d1e53939995c2f562c1`: [CI #42883243171](https://github.com/Iam-2squared/ark-ai/actions/runs/42883243171) was **IN_PROGRESS (all six jobs)** at latest read before this report. Status must be rechecked at the precise final checkpoint HEAD; this report commit itself creates another HEAD.
- No full local pytest/Windows simulation is claimed; GitHub Actions is the only cross-OS evidence. All 3 new Planner test cases and changed Memory test must pass their **exact** SHA checks before being called validated.

## Frozen state and next plan / 今後の方針

Draft PR #5 remains frozen/unmerged, paused Draft UI PR #9 untouched, and frozen V1/V2/Local UI/Launcher/ObservationEnvelope v1 contracts/evidence unchanged. No UI features, frontend tests/integration, physical-PC operations, credentials, external services, paid compute, training, protected final evaluation, promotion, real action or main merge.

1. Check the latest exact-HEAD 6-job Windows/Ubuntu matrix, inspect real failures and minimally repair only what is substantiated.
2. Preserve Memory fail-closed WAL path handling and CAS generation, test sidecar/expiry startup independently from CAS if reproducible; never change production custody rules solely to silence a test.
3. Add retained, independently held Planner state witness or a conservative multi-store read interface only after prerequisite GREEN, with no authorization or executor; preserve all UNKNOWN WRITEs as manual-only.
4. Keep context revocation/retention, proactive/observation mock state, free V3 path/identity/approval guards as independent work lanes. Final JARVIS/V3 status **NOT_PASSED**.
