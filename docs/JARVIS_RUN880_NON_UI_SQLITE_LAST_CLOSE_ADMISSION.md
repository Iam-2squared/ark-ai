# ARK AI Run880 — Non-UI SQLite final-unlink admission hardening

## Scope and authority

**Work basis:** `679567a07d7ebf39bdf02a82ee932076c44e385c` (Run879 checkpoint). **Complete source/test HEAD:** `947ef4215f6f34ce814f161d5a1f5e7bd3229b34`. **Target:** Draft PR #8 (`research/jarvis-foundations`), unmerged. This is local, disconnected foundation work under a no-new-paid-services boundary, **NOT** real execution authorization, external-effect exactly-once proof, authenticated consent or physical-PC testing.

The previous Run879 complete checkpoint [CI #43635703737](https://github.com/Iam-2squared/ark-ai/actions/runs/43635703737) is **GREEN 6/6**, Windows/Ubuntu × Python 3.11–3.13 (verified individual jobs). It does **not** cover Run880 source/test changes.

## Four coherent implementation + regression packages

All packages address the same observed Windows/SQLite last-client-close race class: a pathname `lstat` may return an **already-unlinked regular** journal/WAL/SHM inode with `st_nlink == 0`. Rejection must remain strict for symlinks, hardlinks, special files, persistent zero-link inodes and orphan sidecars.

1. **Planner synthetic journal**: `src/ark/agency/planner_journal_review.py` source commit `c739e6a7450a623705c7491018102c2064565277`, test `tests/test_planner_transient_sqlite_sidecar_run880.py` commit `5a8d0d0e2a1e7e4fe969244cc2a3f5ab473f560e`. Source retains the existing diagnostic `synthetic plan journal sidecar unsafe or orphaned`; it re-`lstat`s at most once after a regular, already-unlinked inode, **only when the main DB still exists**. 16 authored parametrized cases.
2. **Durable occurrence fixture**: `src/ark/agency/durable_occurrence_review.py` commit `ebfa84ccb3c6f2c8ea217585a89b1aa14c2f316e`, test `tests/test_occurrence_transient_sqlite_sidecar_run880.py` commit `77a9e38a6750abfb66300f3b6069aefaa10fd387`. Orphans are still rejected before recheck, as are aliases and persistent zero-link inodes; same established rejection classifications. 18 authored cases.
3. **WRITE Slot Ledger**: `src/ark/agency/disconnected_write_slot_ledger.py` commit `bcd2d71331166bb44475679252d661538211e12e`, test `tests/test_write_slot_transient_sqlite_sidecar_run880.py` commit `8ba060060a32269648021966a82d6cc206ea3e31`. Recheck requires an **existing main** and `create=False`; first-creation/orphans remain refused. 18 authored cases.
4. **Atomic preaction intent/audit ledger**: `src/ark/agency/disconnected_atomic_preaction_ledger.py` commit `0e8144dbc423eabceea1291fcc8d2f95e9417f94`, test `tests/test_atomic_preaction_transient_sidecar_run880.py` commit `947ef4215f6f34ce814f161d5a1f5e7bd3229b34`. Same bounded re-observation for existing ledgers only; sidecars encountered during creation remain blocked. 18 authored cases.

**Total: 4 source files + 4 new path-only test files, 70 authored parametrized cases.** No SQLite schemas, event-chain invariants, PermissionGate semantics, frozen V1/V2/Local UI/Launcher contracts, protected datasets, frontend files or PR #5/#9 branches changed. Exact compare `679567a...947ef42` confirms precisely eight non-UI paths.

Tests cover disappearing last-unlinked regular files, same-name replacement with a new regular inode, symlink/hardlink substitution preserving private targets, continuously unlinked inodes (exactly two observations), nonregular zero-link fake inodes (no retry), and first-creation orphan refusal (no new database created). They only call path preflight on disposable stub files, **never** open a real user DB or execute a ToolBackend.

## Limits and CI custody

The bounded re-`lstat` policy is deliberately **not** atomic descriptor-held path custody. A local attacker with directory write access could still race pathname replacement after the second check. It does **not** settle the root cause of intermittent Windows `-wal` `link_count=0`, Privacy Revocation cross-process loser results, COMMIT-UNKNOWN, cross-store atomicity, authorizing clocks, authenticated provenance, real tool effects or physical-PC behavior.

**Run880 new-work CI (last observed 2026-11-15 around 05:48 JST):** [Planner #43639082483](https://github.com/Iam-2squared/ark-ai/actions/runs/43639082483) **IN PROGRESS** 6 jobs; [Occurrence #43639156598](https://github.com/Iam-2squared/ark-ai/actions/runs/43639156598) **IN PROGRESS/QUEUED**; [WRITE Slot #43639227453](https://github.com/Iam-2squared/ark-ai/actions/runs/43639227453) **QUEUED**; [Atomic Preaction #43639313609](https://github.com/Iam-2squared/ark-ai/actions/runs/43639313609) **QUEUED**. No latest-HEAD six-platform GREEN claim until the exact run completes. New authored cases are not yet CI-confirmed successful.

## Follow-on priority

1. Confirm exact Run880 six-job CI results and classify any failing job using logs; do not weaken alias/no-retry guards. Apply only minimal semantics-preserving fixes by normal GitHub Contents API, or preserve blocker.
2. Investigate Windows/SQLite last-close WAL/SHM and Privacy Revocation cross-process outcomes with independent retained witnesses. A transient pathname improvement is not a complete race solution.
3. Prioritize Memory CAS+expiry coherent snapshot retained epochs, Planner RUNNING→UNKNOWN recovery/terminal dependency projection, and no-auto-replay.
4. Integrate immutable Registry → exact PermissionGate → durable occurrence/intent → audit-before-action → fully disconnected Mock Executor only after exact-head CI evidence.
5. Continue Personal Context privacy, proactive scheduler, observation fixtures, and V3 free-only guards, keeping UI paused, PR #5/#8/#9 Draft/unmerged, and protected gates unopened.

No paid API/service, GPU, training/adapter generation, real Candidate promotion, protected V2 evaluation, external WRITE, new account/credential, irreversible migration, or main merge authorized or executed.
