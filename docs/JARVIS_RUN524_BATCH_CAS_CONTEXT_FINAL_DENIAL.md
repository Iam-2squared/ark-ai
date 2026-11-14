# Run524 — complete registered READ batch, Memory CAS and context recovery denial

**Branch:** `research/jarvis-foundations`, [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8), unmerged. **Latest corrected source/test basis HEAD:** `637e40068df75951efe47da13dfabc60b6c56452` (after clock custody and the two-test message correction). **ARK/JARVIS:** NOT_PASSED. All work is reversible, zero-cost, local/mock-only; no real ToolBackend or context disclosure.

## Package A — full Planner DAG → Registry/PermissionGate → retained SQLite READ witnesses

New `src/ark/agency/disconnected_registered_batch_receipt_set.py` accepts one **ordered evidence item per DAG step**. It verifies the original bounded plan and dependency waves, the complete step count/ordering, registered `act_` call vs disconnected `req_` fixture result, exact READ grant, and separately retained SQLite journal witness through the existing single-step reviewer. Every step and the plan are checked in multiple passes; after all five false-valued authority getters, the entire batch is re-read to detect late mutation. The aggregate is a bounded digest of the per-step diagnostic receipts, not execution evidence.

`tests/test_registered_batch_receipt_set_run524.py` provides **14** cases: one/two-step success without dispatch; omission/duplication/reordering/extra evidence; wrong independent digest, expiry and boolean clock; row tamper; post-denial result rewriting; post-denial journal tamper; exact-False authority. Source `9fab7f0a2b5cc71d1ecaef760b1e4d446813d8b2`, combined source+tests `b12ded3221a8c3c824ea75100721780d6d5997ef`, [CI #41290180715](https://github.com/Iam-2squared/ark-ai/actions/runs/41290180715) was **in progress** when this evidence was drafted.

**Limits:** A wavefront is not proof that dependencies completed. Journals and the caller-held `act_`→`req_` link are independently unauthenticated. Multiple SQLite reads, even repeated, cannot form one cross-database transaction. No backend call, WRITE, automatic replay or external read success is conferred.

## Package B — independent Memory SQLite CAS and expiry regression

`tests/test_memory_concurrent_cas_run524.py` adds **5** deterministic, local tests: two competing updates against the same expected revision (exactly one succeeds), independent-handle stale update denied without phantom event, concurrent unrelated creates retained, duplicate delete not double-logged, inclusive expiry and terminal `expire` event. This is a verification package; **the Memory v1 schema and production source were not modified**.

Test commit `ad70b4c2f1949f6367a26467d83ed49216f0b9bf`; [CI #41290471305](https://github.com/Iam-2squared/ark-ai/actions/runs/41290471305) was **in progress** at drafting. Concurrency evidence is for local SQLite behavior and does not authenticate an external writer, user consent, or erasure of backups.

## Package C — restarted Personal Context replay final denial and durable tip

In `src/ark/personal_context_replay_recovery.py`, result scalar carriers are now rechecked **after each** exact-False no-authority getter, with an additional SQLite durable-tip verification after the **last** getter. A caller-supplied, retained witness remains separate from the database and is not an attestation. The final report cannot silently gain context disclosure, Tool dispatch or replay authority through a synthetic false-valued callback or a newly mutated local DB.

`tests/test_personal_context_replay_final_denial_run524.py` adds **9** test cases: clean empty-ledger restart, three late result changes, three forbidden authority values, equal-text path retargeting, and final getter-driven SQLite schema drift. Source `fe7a0e67fa95a10d123643cd9aecabf798ad1490`; combined source+tests `83863d8ab33e279fcbd2ffc6ca1ebcaf4c32102c`; [CI #41290630015](https://github.com/Iam-2squared/ark-ai/actions/runs/41290630015) was **in progress** at drafting.

## Package D — synthetic clock event chain, denial-only custody

`src/ark/agency/synthetic_clock_sequence_review.py` now checks its constructed witness's exact carrier identity and scalar values after **each** no-authority getter. Before promoting each newly constructed candidate into a next chain link it also verifies that a late false-valued denial getter could not rewrite the digest, source or timing fields. Synthetic monotonic/wall clock samples are caller-provided and never a trusted-clock assertion or ToolBackend permission.

`tests/test_synthetic_clock_final_denial_run524.py` adds **13** cases: bounded two-sample chain, separately retained local prefix; three non-False authority returns; three false-valued getter mutations; three regressed/replaced source or time samples; a generator finalizer mutation; and empty evidence refusal. Source `8599ff5f64488bc9d498a5adcf42714cf9671d88`, source+test `5b3afc32865dfd6fad555452034d64ce38b5b87e`; [CI #41290856984](https://github.com/Iam-2squared/ark-ai/actions/runs/41290856984) was in progress at drafting.

## Prior-failure semantic-preserving repair

[CI #41290630015](https://github.com/Iam-2squared/ark-ai/actions/runs/41290630015) on the initial privacy source/test HEAD failed the legacy `tests/test_context_replay_result_final_epoch_run488.py` assertion on Ubuntu: the same callback mutation was correctly rejected with the **earlier** `review result gained authority` diagnostic instead of `review result changed` (2 tests, not authorization bypass). Updated the legacy test regex to accept **either fail-closed diagnostic** while still requiring the exact exception. Test-only fix `637e40068df75951efe47da13dfabc60b6c56452`, [new exact-head CI #41290984879](https://github.com/Iam-2squared/ark-ai/actions/runs/41290984879) initially queued. No production safety condition was loosened.

## Validation, frozen boundaries and blockers

**41 new pytest cases in this PR = 14 + 5 + 9 + 13**, authored but NOT an independent local PASS count. [Previous Run523 checkpoint CI #41286623023](https://github.com/Iam-2squared/ark-ai/actions/runs/41286623023) became **6/6 GREEN**, as did the previous final corrected source CI #41286431721. Each Run524 HEAD and later documentation/checkpoint HEAD must receive its own evidence; no inherited PASS.

No paid/external compute, API, GPU, subscription, model acquisition, real Candidate, protected V2 evaluator opening, credentials, actual READ/WRITE backend, autonomous context release, notification, destructive deletion or main merge. No change to Memory v1 or Agency frozen contracts, V3 Contract 1, V1/V2/Local UI/Launcher freeze or canonical project-status history. PR #5/#8 remain Draft/unmerged. Source and witness digests are local consistency diagnostics only.

## Next plan

Resolve any exact-run CI failure without weakening refusals; then extend restart-safe DAG receipt correlation and Memory record/event CAS proof boundaries, trusted-clock audit-before-action, manual-only UNKNOWN WRITE, proactive scheduler occurrence protection, privacy retention and offline observation. Retain all paid/human/physical/protected gates until explicit authorization.
