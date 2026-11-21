# ARK AI Run893 — reflected Planner integer width, process-separated Memory CAS and WAL-phase diagnostics

**Observed at (Asia/Tokyo/JST): 2026-11-15T18:57:29.511+09:00** (ordinary wall clock, NOT a trusted authorization timestamp). **ARK/JARVIS: NOT_PASSED.** Work exclusively on reversible, non-UI, disconnected/free-only ARK foundations. Draft PR #8 stays unmerged; protected PR #5 and paused UI PR #9 are untouched.

## Verified starting state and dependency separation

Initial work basis: Run892 checkpoint `c03e5e3cf023112e1a6aba529b47dcc6369bf6d8`. GitHub Actions [#43697057652](https://github.com/Iam-2squared/ark-ai/actions/runs/43697057652) completed **GREEN in all six Windows/Ubuntu × Python 3.11–3.13 jobs**, observed at this invocation. This evidence applies ONLY to that initial HEAD, not later commits.

Three logically separate non-UI packages were saved with ordinary GitHub Contents API writes. No merge, workflow dispatch, force-push, raw Git-object write, external GPU, paid service, actual ToolBackend or user data occurred.

### Package A — Planner post-constructor integer admission

- Source commit: `cbc474cbe08d60c1eff05deb04ee6a1b706e4d8b`.
- Source: `src/ark/agency/planner.py`. Existing `_admit_frozen_arguments` now rejects reflected exact integer values whose `bit_length()` exceeds 14,000 **before** `ToolCall.request_id` JSON hashing. No frozen ToolCall/PlanStep dataclass edit or actual tool execution.
- Regression test created in `tests/test_planner_reflected_integer_width_run893.py` (5 authored cases). Oversize direct/negative/nested integers are denied before a synthetic hash trap; boundary-width legitimate inputs and originally frozen nested JSON remain usable. Test callback setup order was corrected in commit `d3ec220235848ee4ddeb5f18cd451fc64b051332`.
- Limit: this is a standalone PlanGraph resource guard, not a cross-process sandbox, independent provenance or full post-construction data attestation. Valid accepted inputs retain their original request digest; oversized otherwise representable values may now be rejected by the Planner review even if the frozen ToolCall constructor accepted them.

### Package B — cross-process Memory v1 CAS and global event witness

- New `tests/test_memory_cross_process_cas_restart_run893.py` (3 authored cases), initially committed at `e313851d63f612782994a5c398d10c4076713eaa`.
- A separate Python child interpreter uses only a disposable SQLite database and fixed synthetic owner/scope. It tests parent visibility of a committed revision-2 update, child stale-CAS denial without consuming the next persistent event ID, and unchanged data across namespaces with globally contiguous event IDs.
- Existing Memory v1 schema, event implementation and Frozen V1/V2 gates are unchanged. Process separation is not an authenticated cross-machine writer, independent audit notarization, atomic cross-store transaction or privacy consent.
- Early intermediate CI at [#43700951536](https://github.com/Iam-2squared/ark-ai/actions/runs/43700951536) failed 6/6 at Ruff I001 on new test imports **before pytest executed**. Subsequent normal Contents API compatibility fixes culminated at `4f455acd21983bc87e4d7dd4a0886f97379dc403`, isolating helper imports; no CAS/error semantics were weakened. Intermediate red jobs do not certify Python test outcomes.

### Package C — bounded WAL/SHM subprocess phase/custody aggregates

- Source commit: `5b259f36d69b77b8b079b881da99b3b2cca81a1f`, test commit: `f1a2611741c69a3676dc5391750c00b0b1b63423` (5 authored cases).
- The existing disposable `scripts/diagnose_revocation_wal_processes.py` now reports only aggregate `status_phase_counts`, `durable_verified_iterations`, and `durable_with_ambiguous_reply_iterations` in addition to its established counters. It distinguishes a durable local veto whose other process refused from a case lacking durable readback, and identifies `BOOTSTRAP` vs `REVOKE` failures.
- No child stderr, source path or raw private data is exported. Existing status parser, privacy refusal, readback verification and main exit-code failure rule remain unchanged. Tests monkeypatch only the disposable probe for aggregated scenarios and assert no path echo or retry.
- This does **not** solve the Windows WAL/SHM last-close race, prove owner/file-handle provenance, or authorize automatic retry of an ambiguous write.

## Exact-head CI and open caveats

The run's earliest source-only CI [#43700814043](https://github.com/Iam-2squared/ark-ai/actions/runs/43700814043) was still in progress at the sampled point. Intermediate source/test runs [#43700951536](https://github.com/Iam-2squared/ark-ai/actions/runs/43700951536), [#43701049281](https://github.com/Iam-2squared/ark-ai/actions/runs/43701049281), [#43701113684](https://github.com/Iam-2squared/ark-ai/actions/runs/43701113684), [#43701199139](https://github.com/Iam-2squared/ark-ai/actions/runs/43701199139), [#43701245922](https://github.com/Iam-2squared/ark-ai/actions/runs/43701245922), [#43701360163](https://github.com/Iam-2squared/ark-ai/actions/runs/43701360163) completed FAIL at the same Ruff import-order gate, including versions before the final import isolation. The latest corrected source/test HEAD `4f455acd21983bc87e4d7dd4a0886f97379dc403` started [CI #43701601179](https://github.com/Iam-2squared/ark-ai/actions/runs/43701601179), **IN PROGRESS** at this report's drafting. Do not equate 13 authored cases with 13 passing cases, nor transfer GREEN from an earlier HEAD to a later one.

**Other blockers remain:** cross-process SQLite WAL/SHM path lstat / disappearing-inode race and loser refusal, cross-store COMMIT-UNKNOWN and exactly-once, trusted clock and human consent/privacy custody, physical offline GGUF gate, real external runtime identity and paid-approval gates. Zero credentials, purchases, provider launches or material external actions. Retained local hashes do not independently authenticate authorization.

## Next plan / 今後の方針

1. Confirm exact six-job CI at the latest final source/test and checkpoint HEAD; if FAIL, make only a normal-path, semantics-preserving correction and switch to independent backend work while validation runs.
2. Continue deterministic WAL/SHM loser-vs-durable-winner diagnostics with regular-file/symlink/hardlink/orphan checks intact; no blanket retry of unknown writes.
3. Advance Planner UNKNOWN journal and post-construction request custody, Memory coherent CAS/expiry and retained event continuity, and Registry/PermissionGate/durable audit-before-action under exact-head evidence.
4. Continue offline Personal Context privacy, Proactive/Observation back-end, and free-only V3 guards without touching the frozen V3 approval/evaluation contract, Candidate artifacts, UI #9 or protected PR #5.

**Do not claim a later PASS or authorize action from synthetic fixture evidence.**
