# ARK Run772 — Non-UI Planner / Atomic Cross-Store Manual Recovery, Memory CAS, Privacy

**UTC/JST window:** 2026-11-11 JST. **Initial work-basis** `19be2de0902abe83323a1833561bb626faab5587` (Run771), Draft [PR #8](https://github.com/Iam-2squared/ark-ai/pull/8) `research/jarvis-foundations`. This report is descriptive of code and tests saved in this run, not a final PASS certificate.

## A. Manual-only registered Planner + atomic snapshot join

- New optional backend source: `src/ark/agency/disconnected_registered_planner_atomic_triage.py`. Commit `ee2beef03f2c94fdfcadd27e1dd00c26415805c1`; source Ruff line-budget edit `10fc1b6a4521ee84e4f7687827063124498c780e`.
- Resolves effects from immutable `ToolRegistry`, instead of trusting caller-supplied READ/WRITE labels. Enforces a unique exact occurrence for every registered WRITE and rejects READ-bound, missing or duplicate occurrences.
- Calls existing Planner recovery-fence projection and coherent *single-atomic-DB* batch snapshot reader. Returns only step/effect/fence/local-binding classifications with explicit False dispatch, WRITE, replay, cross-store-atomicity and external-effect flags.
- **Critical limit:** the Planner journal and atomic pre-action ledger are separate SQLite stores and can commit between each other's read. This join does not create a cross-store transaction. Even `LOCAL_MATCH` + recovered RUNNING is `QUARANTINE_WRITE_UNKNOWN` and requires independent manual reconciliation, never automatic retry.
- New regression tests: `tests/test_registered_planner_atomic_triage_run772.py`, commit `756d19f231bd6e9de70bd58b50a078735089eca6`, Ruff import wrap `d94115a02f48040083f6c1f2f79007c1d175f9b0`. **9 parameterized cases**: running/pending/contradictory local bindings, unique occurrence membership, READ contamination, status tamper, stale retained atomic count, deny-only fields. Synthetic backends record zero calls.

## B. Memory CAS independent owner / process integrity

- New `tests/test_memory_independent_owner_process_cas_run772.py` at `f6f4ba912acd299d3728f43376024eddfafcf955`; **2** cases.
- Two independent operating-system Python processes update *different* owner-scoped Memory rows in one SQLite file. Both should commit, global event IDs remain contiguous, each row advances exactly one revision with an independent generation token, and stale reuse is denied.
- A retained token from owner A must not update owner B. Only local disposable SQLite is involved; no consent, independent writer attestation, or external exactly-once conclusion.

## C. Personal Context replay privacy across processes

- New `tests/test_context_multiprocess_replay_race_run772.py` at `23608611326376419dcb310c1232ae9af182263b`; **2** parameterized cases.
- Two independent interpreters contend on an identical or distinct context request while holding the same stale genesis witness: exactly one local reservation succeeds. A duplicate remains refused after reopen; a different losing request can be attempted with the fresh witness.
- Fixture private text must not appear in SQLite bytes; hashes are still sensitive linkable metadata. Receipts grant no context disclosure, trusted approval, or replay rights.

## D. Evidence, review limits and gates

- Prior exact Run771 checkpoint CI [#42869651374](https://github.com/Iam-2squared/ark-ai/actions/runs/42869651374), HEAD `19be2de0902abe83323a1833561bb626faab5587`: **SUCCESS, Windows/Ubuntu 3.11–3.13 6/6**. This only validates that historical HEAD, not Run772.
- New package CI identities: [#42878953007](https://github.com/Iam-2squared/ark-ai/actions/runs/42878953007) (source), [#42879217898](https://github.com/Iam-2squared/ark-ai/actions/runs/42879217898) (Memory), [#42879561776](https://github.com/Iam-2squared/ark-ai/actions/runs/42879561776) (Context), [#42880054658](https://github.com/Iam-2squared/ark-ai/actions/runs/42880054658) (Planner test), [#42880367648](https://github.com/Iam-2squared/ark-ai/actions/runs/42880367648) and [#42880409165](https://github.com/Iam-2squared/ark-ai/actions/runs/42880409165) (format-only revisions). At report drafting, these were **IN_PROGRESS/QUEUED**; latest exact-head 6/6 PASS is **UNVERIFIED**. Any failures require actual logs and normal minimal correction.
- **13** new parameterized tests in **3** backend test files, **1** optional non-UI backend source module. No local full-test run claimed. No UI, frontend features/tests/integration, UI PR #9, or frozen contract files modified.
- Draft PR #5 learning/evaluation stays untouched/unmerged and retains its human/paid gate; paused Draft UI PR #9 likewise untouched/unmerged. V1/V2/Local UI/Launcher and protected evaluation evidence unchanged.
- No paid/external compute or GPU, real Candidate model, protected V2 final eval, credentials, real WRITE/notification/camera/mic, physical-PC action, main merge, promotion, or irreversible change. Local integrity evidence is NOT authenticated consent, source provenance or cross-store exactly-once proof.

## Next plan / 今後の方針

1. Verify the **exact final PR #8 HEAD** CI matrix, identify any failing jobs from logs, repair only the observed issue by normal permitted GitHub Contents writes.
2. Exercise Planner/atomic manual review under cross-database interleavings and retained witness loss without upgrading any local status to dispatch or automatic replay.
3. Extend Memory CAS expiry/recreation/ABA and COMMIT-UNKNOWN, plus Personal Context revocation/retention and proactive startup integrity with independent process fixtures.
4. Continue synthetic observation and free V3 path/identity/approval pre-compute review, retaining all user confirmation, frozen, paid, Candidate and protected evaluation gates. ARK/JARVIS/V3: **NOT_PASSED**.
