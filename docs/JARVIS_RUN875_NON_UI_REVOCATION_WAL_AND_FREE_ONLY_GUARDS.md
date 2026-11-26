# Run875 — disconnected revocation WAL diagnostics and free-only guard oracles

**Recorded at (Asia/Tokyo/JST): 2026-11-15T00:44:13.078+09:00.** **Work basis:** Run874 checkpoint `3660db2c2ff8ee23873342c9b1e91218bf8c104f`; latest **source + tests** basis `8ce3ea4562255a5d03b71bfa299d5047cb1357a4` at authoring. This report is non-authoritative synthetic evidence, never trusted audit time, human approval, independent provenance, or real external side effect. **ARK/JARVIS: NOT_PASSED. UI work remains paused.**

## Package A — actual synthetic revocation WAL final-close probe

- Extended the existing disposable real-ARK Memory/ActionAudit WAL test probe to `kind=revocation`, using a brand-new `TemporaryDirectory`, the actual `SyntheticContextRevocationLedger` schema and a synthetic `MemoryScope("disposable-owner","profile")`.
- The **temporary fixture alone** explicitly enables SQLite WAL, then persists one veto, holds an open SQLite reader in another local process, captures the old `-shm` descriptor's link state before and after final close, and requires a **cold `require_existing=True` reopen to still deny that exact scope**. This neither changes the production ledger journal policy nor fixes the known Windows WAL/SHM race.
- A first source change created a temporary SQLite journal-mode connection via `with sqlite3.connect(...)`, which **does not close the SQLite handle**. A follow-up minimal correction uses `contextlib.closing` so the final-client-close probe does not accidentally retain a third connection. The corrected source is saved in commit `8ce3ea4562255a5d03b71bfa299d5047cb1357a4`; the original source contribution is `352f3aac7d0ca31434afb64fe44e3c511cb31fc7`.
- Extended the existing WAL regression matrix to `memory`, `audit`, `revocation` with both keeper states and a second path-free CLI fixture. **Three new parameterized scenarios** are authored (commit `0470ac4834904b96d9dbf79956513affcc0f91ee`), *not claimed GREEN on this new code*. On platforms without POSIX `O_NOFOLLOW`, the existing probe returns `UNSUPPORTED` and coverage remains explicitly limited.

## Package B — detached free-only V3 packet mutation matrix

- New `tests/test_v3_free_only_packet_metamorphic_run875.py` (commit `14ee6124a73d72dc015a6ee360a1b51b4090244d`), **13 authored scenarios**. One positive canonical synthetic packet must return all false for provenance, compute, training and promotion authorization. Nine controlled payload mutations challenge device and tokenizer exact binding, measured capacity, VRAM ordering, time budget, exact boolean typing and oversized numeric/device evidence. Three framing attacks challenge trailing bytes, unexpected authority field and duplicate JSON keys.
- It invokes only the existing detached packet reviewer on in-memory synthetic JSON; **no PR #5 contract change, Candidate, hardware probe, protected evaluation or training**.

## Package C — deterministic startup DAG oracle

- New `tests/test_startup_readiness_dag_oracle_run875.py` (commit `0284c28dc6056a16e1eb2de2e9de46b1dc9b9b9d`), **10 authored scenarios**. Eight deterministic seeded 14-node dependency DAGs compare evaluator effective states and sorted local root blockers to an independent topological oracle and verify input-order invariant digest. Separate fixtures show that DEGRADED is not itself BLOCKED and that a cycle cannot be reported READY.
- Synthetic probe states still **never attest to real startup readiness or authorization**.

## Exact evidence and limitations

- Previous Run874 checkpoint CI [#43607878336](https://github.com/Iam-2squared/ark-ai/actions/runs/43607878336): **6/6 GREEN**, Windows/Ubuntu Python 3.11–3.13, previous HEAD only, directly verified this invocation.
- Current corrected source/test HEAD `8ce3ea4562255a5d03b71bfa299d5047cb1357a4`: automatic [CI #43611663812](https://github.com/Iam-2squared/ark-ai/actions/runs/43611663812) **QUEUED at report drafting**. Earlier interim [#43611354520](https://github.com/Iam-2squared/ark-ai/actions/runs/43611354520) and [#43611483926](https://github.com/Iam-2squared/ark-ai/actions/runs/43611483926) had jobs IN PROGRESS. **26 new authored scenarios are not a 6/6 PASS claim**. No local full pytest/Ruff run, physical Windows action, real GGUF or user data.
- Exact compare Run874 to corrected source+tests shows only **four non-UI paths** changed (one disposable script, one existing regression module, two new offline test modules). Frozen V1/V2/Local UI/Launcher code/contracts/evidence untouched. No cross-store atomicity, independently retained receipt, consent, auto-retry or real effect proven.
- Existing privacy revocation multi-process loser and Memory/ActionAudit WAL/SHM transient last-client-close issues remain **unresolved**; this probe supplies narrower reproducible evidence, not a production bypass of path/alias rejection.

## Next plan / 今後の方針

1. Confirm the exact corrected source+tests HEAD on all six CI jobs, repair any actual FAIL via normal GitHub Contents API only, and never duplicate a workflow run.
2. On isolated disposable data, identify whether the revoked loser was denied by source-path sidecar, SQLite busy, schema or durable marker classification; **do not relax any deny or authorize automatic retry**.
3. Advance independent Memory/ActionAudit COMMIT-UNKNOWN and Planner crash recovery, CAS/expiry coherent snapshots, exact immutable Registry/PermissionGate plus audit-before-action; only mock/disconnected executor after exact-head GREEN.
4. Keep PR #5/#8/#9 Draft/unmerged, PR #9 and all UI untouched; no paid or external GPU/API, Candidate creation/promotion, protected V2 final evaluation, secrets, real tool dispatch or main merge.
