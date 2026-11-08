# Run713 — non-UI CI recovery, Memory pre-access, READ WAL, clock digest custody

Work basis (independently observed PR #8 HEAD before writes):
`d0c9b81273e01d3ca9cd45406bbac330b535112a`.
Branch: `research/jarvis-foundations`, [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8).
Status: **FREE-ONLY, SOURCE/TEST SAVED, latest exact-head 6/6 GREEN UNVERIFIED**.
No V1/V2/Local UI/Launcher frozen contract, frontend, main, PR #5 or PR #9 changed.

## A. Exact-log context-prefix CI repair

Run712's final [CI #42482355336](https://github.com/Iam-2squared/ark-ai/actions/runs/42482355336) failed in all six Windows/Ubuntu Python 3.11–3.13 jobs: the Ubuntu 3.11 log reports **4 failed, 11,108 passed, 1 skipped**; the Windows 3.13 log reports **4 failed, 11,049 passed, 60 skipped**. All four failures were stale error-message expectations in these three existing tests:

- `test_context_prefix_final_denial_run518.py`: both a forged report denial property and a forged retained witness property were preinstalled. The implementation now rejects the **report authority** before reading the retained witness, not the older witness-first error.
- `test_context_prefix_original_denials_run614.py`: a preinstalled `json.dumps` replacement is rejected as **digest implementation changed** before the callback can install an authority property.
- `test_context_prefix_original_result_carriers_run659.py`: the two parameterized SHA/JSON replacements are rejected by the same early digest identity gate before a forged result field can execute.

Corrected the diagnostic assertions only. The tests still assert **zero hostile getter execution** and no authorization. Early push CI exposed two Ruff E501 lines (103 > 100) and an unrelated new import-order I001. Those three lint issues were subsequently corrected through ordinary GitHub Contents API updates. Neither production privacy checks nor original denials were weakened.

## B. Memory dual-review pre-access input custody

Source:
- `src/ark/memory/ambiguous_commit_pair_review.py`
- `src/ark/memory/generation_cas_outcome_review.py`

Both independent manual/read-only CAS ambiguity reviewers used to inspect `type(proposed.scope)` before checking whether the original frozen `MemoryWrite`/ `MemoryScope` field descriptors or hooks had been reflectively replaced. The existing, opt-in `_require_original_generation_inputs()` check is now invoked **before the first proposed-field read** and again in the stable callback boundary. A `MemoryGenerationCASRejected` is translated into each review's own fail-closed diagnostic error.

Added `tests/test_memory_ambiguous_proposal_preaccess_run713.py`: 24 interpreter-isolated hostile carrier cases (2 reviewers × 12 field/hook mutations), plus 2 healthy manual-only controls = **26 tests**. Each hostile test sets up disposable local SQLite first, then replaces a class-level field/lookup/constructor hook and requires rejection with **no invocation of the injected code and unchanged row content/revision**. No write retry, caller attribution or external effect follows from a matching row.

## C. Planner READ-journal WAL snapshot evidence

Added `tests/test_read_journal_wal_recovery_snapshot_run713.py` with **2 tests** using separate local SQLite handles: an append committed after the first read-snapshot scan and a deletion of the disposable fixture's last receipt committed after the first scan. A recovery spanning a WAL writer should return the *same old* read snapshot, not mix receipt rows and hash tips across epochs. A *new* read must notice the changed current tip and reject an outdated independently retained witness. This is digest-only fixture recovery, **not evidence that any READ tool executed**.

## D. Synthetic trusted-clock boundary remains explicitly untrusted

Source: `src/ark/agency/synthetic_clock_sequence_review.py`.
The caller-provided, disconnected clock sequence now pins import-original `hashlib`/`sha256`, `json`/`dumps`, and the exact genesis string object before reading any sample iterator or retained witness, and checks identity again at synthetic callback boundaries. A byte-equal genesis replacement is still a new epoch and is rejected. The clock remains unauthenticated and cannot authorize dispatch or replay.

Added `tests/test_synthetic_clock_digest_identity_run713.py`: **5 preinstalled substitutions**, **2 reentrant replacements after hashing**, and **1 normal deny-only control** = **8 tests**. No hardware time, external GPU, real tool, live notification or account connection is used.

## Evidence and limitations

- **New tests authored:** 26 Memory + 2 READ WAL + 8 clock = **36**. Prior CI failing legacy parametrizations corrected: **4** (spanning three test files); no source safety downgrade.
- Initial CI failure: [#42482355336](https://github.com/Iam-2squared/ark-ai/actions/runs/42482355336), **6/6 FAIL** for four obsolete assertions. Early fix [#42486264716](https://github.com/Iam-2squared/ark-ai/actions/runs/42486264716) and Memory intermediate [#42486600883](https://github.com/Iam-2squared/ark-ai/actions/runs/42486600883) **6/6 FAIL** from known Ruff E501/I001 issues; corrections are in later commits. These runs are **not** evidence for the final source.
- The SHA/JSON guard, all Memory pre-access cases, READ WAL cases, and clock cases require full Windows/Ubuntu Python 3.11–3.13 **exact-head CI**. No full local pytest/Ruff run or device execution is claimed. A queued/in-progress CI is not GREEN.
- Frozen boundaries: V1/V2/Local UI/Launcher evidence unchanged; PR #5 stays draft and protected, PR #9 stays draft and **UI PAUSED**. No paid compute/API/service, Candidate generation, protected evaluation, main merge, raw Git bypass, force push, real executor, sensor capture, irreversible account/data action, or automatic COMMIT-UNKNOWN retry.
- Residual risks: SQLite-local hash chains do not independently authenticate writer or retained witness, a read-only WAL snapshot is not durable external custody, and caller clock inputs are not trusted time. Action Audit full-history verification retains O(N) cost and must not be silently weakened.

## Dependency-aware next work

1. Inspect **final exact-head CI** for all six jobs and repair only log-proven failures. Avoid duplicate workflow launches and overlapping source work during CI.
2. Once Memory + Planner lower-layer fixes are exact-head GREEN, pursue COMMIT-UNKNOWN manual reconciliation and per-step persisted READ status evidence; no automatic replay.
3. Then strengthen immutable registry-bound authorization, occurrence/replay fencing, audit-before-action, and disconnected mock integration. No real execution without explicit gates.
4. Continue separate privacy-safe context/proactive/observation fixtures and free-only V3 guard review without crossing protected approval/evaluation boundaries.
