# ARK AI — Run770 non-UI safety work: post-COMMIT custody, SQLite atomic binding, Planner retained tail, Memory generation CAS

**Saved evidence draft at:** 2026-11-11T01:57:37.668+09:00 JST (administrative host-clock sample; not authenticated ARK time, human consent or authorization).
**Initial exact work-basis HEAD:** `ecd640d3d3605765d7ccea9ac1b7f125d99ff52c` (Run769 checkpoint).
**Branch:** `research/jarvis-foundations`, [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8), no merge.
**Scope:** free-only, non-UI source + isolated synthetic/local SQLite regression tests. No paid/external compute, V2 protected evaluation, Candidate adapter/weights, live ToolBackend or external effects.

## A. Personal Context: deny executable receipt hooks after local COMMIT

- Source: `src/ark/personal_context_replay_ledger.py`, `ea3bcdf6f99bba0c57e5417dc22f606326f8e007`.
- Tests: `tests/test_context_receipt_hooks_run770.py`, `1c21538d9a501d0cfc91bafe1fb2e39c4011e9dd`; **3** subprocess-isolated parameter cases (substituted `__new__`, `__getattribute__`, `__getattr__`).
- Import-time constructor, slots, denial descriptors and the three lookup/allocation hooks are verified before and after the post-COMMIT receipt, including a final post-getter review. If any injected callable is present, the local SQLite request reservation survives, the substituted callable must not run, and the previous witness cannot authorize a second reservation. The return value cannot be treated as a rollback, consent or disclosure grant.
- Existing test `tests/test_context_replay_postcommit_custody_run485.py` repaired at `74022580fac279833797770dc758f0a684a284f6`: **3** old cases had expected a *later* witness-mutation error from a constructor monkeypatch, but the newer, stronger Run769 constructor pinning correctly rejects the monkeypatch *before* it executes. The corrected test now asserts early denial, no injected callback, one actual SQLite COMMIT, stale-witness retry rejection. No production guard removed or frozen test weakened.

## B. Registered atomic pre-action snapshot: unpatchable scalar witness comparison

- Source `src/ark/agency/disconnected_atomic_binding_snapshot_review.py`: `abe38a54e215b5235cc483f089d1240850a1962b`.
- Tests `tests/test_atomic_binding_witness_eq_guard_run770.py`: `dca8857402687ff6de7092957fbd08fbb5e57b4c`, **2** parameter cases (identical and forged tip).
- The read-only single-SQLite-snapshot registry/intent/audit comparison no longer invokes patchable `AtomicPreactionWitness.__eq__`. It compares exact `count`/`tip_sha256` scalars with the separately retained witness. Maliciously replaced equality cannot accept a different chain or execute during the pre-action review. A locally equal result is **not** trusted approval, dispatch permission, independent custody or external outcome proof; all actual WRITE remains quarantined.

## C. Planner: retained journal prefix equality cannot be rebound

- Source `src/ark/agency/planner_journal_review.py`: `26a12b442e8d54e5a627c33a9313de5644eacd07`, formatting-only follow-up `5d35087994e4cb1a2993daadc7969a424d9fee92`.
- Tests `tests/test_planner_retained_tail_eq_run770.py`: `10d4cfb8d21c4853ef43af2c5ec35da554cbcc44`, **4** parameter cases (READ-only recover vs CAS append × original vs forged retained hash); lint-only function syntax `0194a02d916d8431131d6903fd0e96fb98e985ae`.
- Both `recover(retained=...)` and `append(..., retained=...)` check the canonical stored event-prefix five scalars against the previously pinned caller values without executing `SyntheticPlanTail.__eq__`. A forged prefix rejects; a valid persisted RUNNING state remains **ambiguous** and **never auto-replayed or dispatched**. No PlanGraph, frozen contract, execution pipeline or permission semantics changed.

## D. Memory: opt-in generation CAS inputs deny executable equality/hash replacement

- Source `src/ark/memory/generation_fenced_cas.py`, `e36d3cd29f49d3e85860b8d7ada6069ed0ee58e4`: import-pinned `MemoryScope`/`MemoryWrite` `__eq__` and `__hash__` in addition to preexisting constructor, fields and attribute hooks. Prevents accepting a class-level substituted equality callback while comparing an observed existing row to caller scope in the opt-in generation path, before private DB reads/writes.
- Tests `tests/test_generation_cas_equality_hook_run770.py`, `4d81b16eede3d9b1c55919517d53b2fe8ea07232`, **8** parameter cases (scope/write × eq/hash × observation/update). The original v1 database row and revision must remain unchanged; no injected callable invoked; no external-action or consent authority.
- Frozen Memory v1 public API, schema and evidence are unchanged; this only tightens a separately opt-in non-frozen path.

## CI failure diagnostics and exact-SHA limitations

- Historical prior success: [CI #42853532414](https://github.com/Iam-2squared/ark-ai/actions/runs/42853532414) on `bda2cd87...`: **Windows/Ubuntu × Python 3.11–3.13, 6/6 GREEN**. This success does **not** verify this Run770 work.
- [CI #42854956071](https://github.com/Iam-2squared/ark-ai/actions/runs/42854956071) on initial Run769 HEAD `ecd640d3...`: **6/6 FAIL**; actual Ubuntu 3.11 log reports 3 tests expecting old postcommit witness mutation when constructor now correctly refuses the injected function first (12,654 other tests PASS, 1 skipped). Repaired at `74022580...`.
- [CI #42858821702](https://github.com/Iam-2squared/ark-ai/actions/runs/42858821702) at `10d4cfb8...`: **6/6 FAIL** Ruff E731 two test-only lambda assignments. Replaced with a nested `def` at `0194a02d...`.
- [CI #42859090169](https://github.com/Iam-2squared/ark-ai/actions/runs/42859090169) at `0194a02d...`: observed Ruff I001 due one extra blank line in test import block; corrected normally at `7d5097ba0e7cf3ad0bfadb857925db35562f9173`, without changing test meaning.
- [CI #42859468383](https://github.com/Iam-2squared/ark-ai/actions/runs/42859468383) at `7d5097ba...`: Ubuntu 3/3 FAIL and Windows in progress at the new log review. Actual Ubuntu 3.13 log shows **1 fail / 12,665 pass / 1 skipped** in old `tests/test_context_replay_original_receipt_epoch_run594.py`. The old test expected a patched `__getattribute__` hook to run and mutate an equal-ID receipt, whereas the stronger Run770 receipt descriptor fence now refuses it *before executing*. The old test was corrected via normal Contents API at `b47cf62ddc00f29e31644b3d0f04ac8beaac8484` to assert zero injected executions, one durable COMMIT and stale retry rejection. No production guard relaxed.
- [CI #42859739808](https://github.com/Iam-2squared/ark-ai/actions/runs/42859739808) at `e36d3cd...`: six jobs **IN PROGRESS** at last inspection. New D-test and subsequent report/checkpoint commits may cause later workflows. Latest **exact-HEAD 6/6 GREEN UNVERIFIED** until six job conclusions match that SHA.
- No local full pytest claimed (repository not clonable in isolated container; verified only GitHub job logs/status and source semantics). Work preserves strict failure, contracts and provenance checks; no duplicate manual workflow dispatch.

## Boundaries, blockers, next

PR #5 V3 remains protected, Draft/unmerged; paused UI PR #9 untouched, Draft/unmerged; PR #8 Draft/unmerged. Frozen V1/V2/Local UI/Launcher/ObservationEnvelope v1, protected V2 final evaluation, and main unchanged. No UI/frontend writes. No paid/external GPU/API compute, real Candidate, physical PC step, external ToolBackend WRITE, real proactive notifications/capture, secrets/account changes, destructive operations, automated promotion or main merge.

**Not proven:** independently held trusted-clock/issuer/approval custody, authenticated human consent, local filesystem anti-tamper, cross-store atomic transactions, or exactly-once real-world side effects. Any committed-but-response-UNKNOWN external WRITE requires manual reconciliation and **must not be automatically retried**. Candidate and real GPU actions remain blocked on approval/identity/cost/licensing gates.

**Next plan / 今後の方針:** (1) exact-HEAD CI across Windows/Ubuntu 3.11–3.13, narrow log-based fixes only; (2) scoped Memory generation/COMMIT-UNKNOWN and high-water/ABA independent witnesses; (3) Planner persisted terminal propagation and READ/WRITE recovery under crash; (4) immutable Registry + exact PermissionGate + preaction audit and disconnected mock-only Executor integration only after lower-layer exact-head GREEN; (5) Personal Context privacy/retention and proactive clock/startup/observation fixture work; (6) V3 offline path/approval/identity reproducibility guards without any paid or protected step. **ARK/JARVIS/V3 NOT_PASSED**.
