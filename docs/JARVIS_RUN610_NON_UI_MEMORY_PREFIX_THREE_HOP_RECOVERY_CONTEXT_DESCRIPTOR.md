# ARK AI — Run610 non-UI core evidence (2026-11-05 JST)

Status: **reversible, disconnected, local-first implementation + regression fixtures** on Draft PR #8. This is not a frozen contract, authorization, full JARVIS PASS, production dispatch approval, or a statement that CI was already GREEN. UI development is paused.

## Package 1 — Memory event-prefix local high-water integrity

Work basis: Run609 checkpoint HEAD `38ee0708607cd3bc7ef30af1e5c4d290374c3d46`.
- Source `src/ark/memory/sqlite_event_prefix_review.py` saved at `b5929ffc30c1441993f759befcf06dbc84da2542`. The read-only Memory event-prefix transaction now compares the global `memory_events` tail against SQLite's `sqlite_sequence` high-water mark, including the case where all events were deleted after a committed append. It does not trust the marker as independent custody: deliberate coordinated modification of events and sequence can evade this local check.
- Tests `tests/test_memory_event_prefix_highwater_run610.py` saved at `bc37b8c8a7b97342610f4d01614fc7bd24fe3e5d`: four corruptions (tail deletion, full history deletion, advanced high-water, removed sequence), an erased fully terminal history, and the ordinary empty/append/read-only path. **6 parameter-expanded cases authored**, not independently claimed as local PASS.
- Does not rewrite Memory rows, schema, historical events, or frozen contracts. Does not infer that a matching event prefix authenticates a writer or gives permission to disclose data.

## Package 2 — Planner three-hop restart classification

- Tests `tests/test_mixed_recovery_three_step_propagation_run610.py` saved at `86a178429da24763efd433059c178769aeca12be`.
- **72 parameter-expanded cases authored**: 56 three-hop state/effect combinations; 4 reserved-WRITE vs unreserved READ chains; 12 fan-in mixtures of terminal and uncertain parents. Verify that PENDING descendants inherit terminal/uncertain holds, WRITE is never marked mock-ready, and each entire review remains deny-only.
- Uses existing `src/ark/agency/disconnected_write_recovery_fence.py` without altering its rules. Pure detached claims, no SQLite mutation or real ToolBackend calls. A mock-readiness classification is **never execution authorization**, and UNKNOWN WRITE remains quarantined.

## Package 3 — Personal Context replay witness static authority

- Source `src/ark/personal_context_replay_ledger.py` saved at `5bd6ce3b7ba689a7b3dc938ce3897110eacd7b4c`. `_check_witness` now verifies the import-original `OfflineContextReplayWitness` class and `independent_custody_proven` descriptor **before** any property invocation. A counterfeit False-returning property cannot execute side effects during read, restart or retained-prefix checks.
- Tests `tests/test_personal_context_witness_original_denial_run610.py` saved at `f62576dad61acf14731578abd7c83db18c0c0dc0`: three getter-entry paths, counterfeit class identity, ordinary empty-archive retained-prefix. **5 parameter-expanded cases authored**.
- No actual private content export, consent inference, revocation suppression or real action dispatch.

## CI and verification discipline

- Last prior exact checkpoint Run609: `38ee0708607cd3bc7ef30af1e5c4d290374c3d46`, [GitHub CI #41862274776](https://github.com/Iam-2squared/ark-ai/actions/runs/41862274776) **6/6 GREEN** (Ubuntu/Windows Python 3.11–3.13; confirmed in this invocation).
- New source/test CI: [#41870297999](https://github.com/Iam-2squared/ark-ai/actions/runs/41870297999) (Memory test HEAD), [#41870556196](https://github.com/Iam-2squared/ark-ai/actions/runs/41870556196) (Planner test HEAD), [#41870909413](https://github.com/Iam-2squared/ark-ai/actions/runs/41870909413) (Context test HEAD). **Final verdict to be recorded only from exact job results.** No duplicate CI run was manually triggered.
- New authored test count **83 (6 + 72 + 5)**. Authored tests are not automatically PASS; the latest exact checkpoint HEAD will have its own CI.
- No local clone or local pytest evidence is claimed. GitHub Contents API is the only used write path, with a re-read of the PR HEAD before each write.

## Frozen and paid/approval boundaries

Do not modify V1/V2/Local UI/Launcher frozen boundaries, PR #5 pre-paid-compute and protected evaluation gates, or paused UI PR #9. Keep Draft PR #5, #8, #9 unmerged. No paid/external compute, paid model API, secrets, account connections, candidate weights/adapters, protected V2 final evaluation, automatic Candidate promotion, physical-PC action, filesystem/network ToolBackend, independent clock, actual erasure or consent proof. A DB-local hash or sequence cannot provide independent provenance.

## Next plan / 今後の方針

1. Verify current exact-head six-job CI and repair only log-supported defects through the normal GitHub Contents path.
2. Examine full CAS generation/uncertain COMMIT evidence and retained Memory row-event coherence without automatic retries.
3. Extend multi-step Planner recovery and bound registry/permission/occurrence/audit only once lower-layer exact-head GREEN is available.
4. Independently review proactive/observation fixture provenance, Personal Context privacy lifecycle and free-only V3 guard paths, without UI work.
