# Run937 — independent non-UI Memory, Proactive and Planner regression packages

**Authored at (Asia/Tokyo/JST): 2026-11-17T15:49:21+09:00** — reporting wall clock only, **not** trusted execution/audit time.

**Scope:** `research/jarvis-foundations` / [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8), no UI work. This document is a source/test change report, **not** an authorization or a claim that JARVIS has passed.

## Exact work basis and three saved packages

- **Work basis:** Run936 checkpoint HEAD `b726e98babfdd531d50a907d80159bbc510c8897`.
- **Memory due-page isolation** [`2ce52a18`](https://github.com/Iam-2squared/ark-ai/commit/2ce52a189dfb6dc81614836d657ec7d67d231cc7): 6 parameterized cases in `tests/test_memory_scoped_expiry_foreign_blob_run937.py`. Each uses disposable SQLite, one healthy owner/namespace with due and live rows and one corrupted foreign-owner/foreign-namespace due row. A scoped bounded expiry should remove only its own due item, append the matching event, survive cold reopen, and not hydrate/repair the foreign BLOB storage class.
- **Proactive interval cross-process** [`e9d8849e`](https://github.com/Iam-2squared/ark-ai/commit/e9d8849e629360d21cbc7ba7b84f03c47c05e524): 2 parameterized cases in `tests/test_proactive_cross_process_interval_run937.py`. Two independent Python writers synchronize before attempting the same policy interval. At most one synthetic preparation can commit; a cold reopened ledger has one content-free marker. The test also exercises a distinct later occurrence after the interval and verifies every returned receipt remains *notification/dispatch/replay denied*. Neither scheduled execution nor a trusted clock is proven.
- **Planner nested argument admission** [`93298414`](https://github.com/Iam-2squared/ark-ai/commit/932984145d012d01f775af94a61ffa798167b9ca): 4 cases in `tests/test_planner_reflected_nested_argument_admission_run937.py`. Post-constructor reflected nested fake mapping/sequence and excessive integer magnitudes must be refused before invoking callback-bearing values; a canonical nested ToolCall still builds a ready DAG without execution. This checks independent Planner ingress, not durable action approval.

**Total: 12 new authored regression cases (6 + 2 + 4), no production-source or frozen-contract edits.** Each package was written through the normal GitHub Contents path after reading the current PR head. No force push, merge, external tool dispatch, credentials, Candidate generation, external GPU, protected evaluation or paid service.

## CI and evidence boundary

- Baseline Run936 checkpoint `b726e98babfdd531d50a907d80159bbc510c8897` [CI #44027382574](https://github.com/Iam-2squared/ark-ai/actions/runs/44027382574): **six of six completed GREEN**, individually checked for Windows and Ubuntu Python 3.11–3.13.
- Memory `2ce52a18`: [CI #44033708420](https://github.com/Iam-2squared/ark-ai/actions/runs/44033708420), **IN PROGRESS (6/6 jobs in progress)** at inspection.
- Proactive `e9d8849e`: [CI #44033817860](https://github.com/Iam-2squared/ark-ai/actions/runs/44033817860), **IN PROGRESS (6/6 jobs in progress)** at inspection.
- Planner `93298414`: workflow not yet listed on first commit-specific query; **no GREEN claim**.
- A document or checkpoint commit triggers a distinct CI run. Its run ID/status cannot be written in advance or attributed to the preceding test HEAD. If new tests fail, inspect exact job logs and repair only their actual semantics-preserving defect via the ordinary path. **Run937 exact final HEAD all-six GREEN NOT VERIFIED.** No full local pytest has been performed.

## Scope and remaining evidence gaps

Protected V1/V2/Local UI/Launcher evidence and all frozen V3 provenance/evaluation/contamination/reproducibility contracts remain untouched. PR #5 protected Draft and PR #9 paused UI Draft remain unmerged, as does PR #8. The user-required physical Windows GGUF offline gate remains pending. A synthetic event sequence or content-free SQLite receipt **does not prove** consent, external action execution, independent audit custody, rollback resistance, cross-store atomicity or exactly-once effects.

## Next plan / 今後の方針

1. Reconcile latest PR HEAD and run all six CI jobs for the **exact** final checkpoint. Fix proven failures without weakening production safety, or record blockers and switch to another independent lane.
2. Extend Memory WAL/SHM process isolation, targeted CAS/expiry versus foreign data, row/event high-water and ABA correctness on disposable stores only.
3. Strengthen Planner persisted COMMIT-UNKNOWN manual-only classification and terminal propagation; never automatically retry ambiguous WRITE.
4. Verify immutable ToolRegistry, exact-type PermissionGate, durable occurrence and audit-before-action integration only after their lower-level exact-head GREEN evidence. Stay disconnected and deny real WRITE.
5. Continue Personal Context privacy, observation/proactive backend fixtures, startup readiness and free-only V3 guards without UI changes or protected gate overrides.

**ARK/JARVIS overall NOT_PASSED.**
