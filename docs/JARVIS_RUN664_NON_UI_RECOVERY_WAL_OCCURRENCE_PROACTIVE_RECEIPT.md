# ARK AI — Run664 non-UI core: Planner recovery DAG, coherent Memory WAL, occurrence race and proactive receipt preaccess

## Verified work basis and boundaries

- Started on PR #8 `research/jarvis-foundations`, OPEN/Draft/unmerged, at exact work-basis HEAD `0655fab6eead2787cc012d25eb4a7c7e6412691a`. Its exact-head Actions [#42238106481](https://github.com/Iam-2squared/ark-ai/actions/runs/42238106481) completed **six of six GREEN** (Ubuntu/Windows, Python 3.11/3.12/3.13) as confirmed from job records, not inferred from a banner.
- Only reversible/disconnected core and test files on PR #8. No UI/frontend or PR #9 edits, no main/PR #5 merge or V3 training/evaluation, no protected frozen contract or evidence updates, no external compute/API, camera/microphone, credentials, live tool dispatch or real notifications.
- Four coherent work packages; **16 authored regression test cases** does *not* mean latest-HEAD PASS until complete exact-head CI. All timestamps and hashes are local synthetic inputs, never independent attestations of human approval, external effects, consent or trusted time.

## Package A — real Planner replay topology → inert mixed-effect fence

- New `tests/test_planner_projection_dependency_recovery_run664.py`, commit `bf8217cd927d3e5bcbc936b098d8017f5afa2e6a`, **6 cases** (three direct, three parameterized).
- Four synthetic steps: pending root READ, dependent WRITE and READ, independent READ. No pending descendant becomes ready merely because a parent is labeled READY_MOCK_ONLY. Restarted RUNNING root becomes QUARANTINE_UNKNOWN, both dependent steps HOLD_UNCERTAIN and independent READ stays READY_MOCK_ONLY. Root failure causes journal-derived dependent BLOCKED to become TERMINAL; unrelated READ remains inert-ready.
- Duplicate, unknown or wrong-case effect labels are rejected without appending a journal event. Every returned review retains four False-only authority flags; there is no backend invocation or independently verified success receipt.

## Package B — two-handle Memory coherent WAL snapshot

- New `tests/test_memory_retained_two_handle_post_snapshot_run664.py`, commit `053ab4b279ae29d9b8f0b30f38e8ef9b4401ec89`, **3 parameterized cases**.
- A separate SQLite handle commits after first row decoding but before the retained reader's event scan. Target UPDATE, target DELETE→recreate and unrelated-row UPDATE must leave the first row/event view exactly equal to the independently obtained pre-commit baseline. A subsequent new read transaction sees the entire new event tail, with no mixed row/event images.
- A locally consistent prefix/row digest does **not** authenticate a writer, consent, actual Memory disclosure rights, cross-store atomicity, COMMIT-UNKNOWN attribution or automatic retry.

## Package C — concurrently colliding synthetic occurrence reservations

- New `tests/test_registry_concurrent_occurrence_collision_run664.py`, commit `38049733e5c29ae29e290feffc91f57f44193159`, **2 parameterized cases**. Two threads, two initialized SQLite handles, one barrier: either the same token on different occurrences or different tokens on the same occurrence. Exactly one synthetic reservation may commit; the other must reject with a duplicate identity. Reopening the store cannot reserve the losing old identity.
- The registry backend records zero calls; successful synthetic receipt fields remain dispatch_authorized=False, outcome_known=False, automatic_replay_authorized=False. This is SQLite fixture deduplication, not authenticated exactly-once external effects.
- Intermediate CI at source HEAD [#42245534510](https://github.com/Iam-2squared/ark-ai/actions/runs/42245534510) **FAILED on all six** due solely to Ruff I001 import ordering in the new test file. Semantics-preserving import-only correction: `093d8f3b7ded4467227fb58e86351a95d8eafc76`. Corrected CI [#42246034820](https://github.com/Iam-2squared/ark-ai/actions/runs/42246034820) was **IN PROGRESS** at report preparation; never treat older source-head runs as proof for it.

## Package D — proactive receipt preaccess guard before durable write

- Production-source update `src/ark/proactive_synthetic_review.py`, commit `1cda6cd17963d23b93b4a79a5efa1d552e8d8840`. Existing `SyntheticTriggerReceipt` protections pinned only the three False-only authority properties. A frozen slotted dataclass does not prevent replacement of its field descriptors, initializer or getter hooks at class level.
- New static checks pin the import-original `trigger_id`/`prepared_at_ms` slots and `__init__`, `__new__`, `__getattribute__`, `__getattr__` hooks. Reject altered descriptors at prepare ingress, under the write transaction **before COMMIT**, immediately before constructing the post-COMMIT receipt, and immediately **after construction before field access**. This preserves the distinction between a durable COMMIT and a later rejected synthetic receipt; it does not roll back an already committed write.
- New `tests/test_proactive_receipt_preaccess_run664.py`, commit `413f4a07de15ea9e85d30a754b0379daa49c0558`, **5 parameterized cases** for class-level slot, initializer and getter poisoning. Injections are confined to the receipt class, never the global `object.__new__`. Each attempted preparation must reject without executing the injected code or writing a trigger; normal restored receipts stay False-only.
- Pre-import-fix Actions [#42245724342](https://github.com/Iam-2squared/ark-ai/actions/runs/42245724342) and [#42245830041](https://github.com/Iam-2squared/ark-ai/actions/runs/42245830041) are **FAIL** from the same shared Ruff I001. These failures do not establish a proactive source/test semantic defect or success; only exact corrected-head CI can do so.

## CI evidence and next work

- Baseline [#42238106481](https://github.com/Iam-2squared/ark-ai/actions/runs/42238106481): exact prior HEAD 6/6 GREEN.
- First Planner [#42245276964](https://github.com/Iam-2squared/ark-ai/actions/runs/42245276964) and Memory [#42245403754](https://github.com/Iam-2squared/ark-ai/actions/runs/42245403754) were still running at the first mid-invocation CI read (independent heads). They cannot certify later packages.
- Registry [#42245534510](https://github.com/Iam-2squared/ark-ai/actions/runs/42245534510), proactive source [#42245724342](https://github.com/Iam-2squared/ark-ai/actions/runs/42245724342), and proactive tests [#42245830041](https://github.com/Iam-2squared/ark-ai/actions/runs/42245830041): 6/6 FAIL or FAILURE, confirmed from Ubuntu Ruff logs; one common I001 import ordering root cause fixed in the final test-only repair.
- Recheck [#42246034820](https://github.com/Iam-2squared/ark-ai/actions/runs/42246034820) at import-fix HEAD; last sampled **IN PROGRESS**. No manual duplicate workflow reruns.
- **Open verification:** resolve full six-job CI on the exact final result HEAD, inspect failing pytest/assertion logs if present and fix only with normal GitHub Contents safety path. No local full Ruff/pytest, physical GGUF model, consent, action-clock, external writer or hardware evidence claimed.
- Next technical dependencies: independently verified Planner SUCCEEDED receipt linkage before any projection upgrade; Memory COMMIT-UNKNOWN and CAS/ABA/expiry review; occurrence/replay and trusted-clock audit-before-action with exact-type registry/gate (only after GREEN); privacy/erasure, proactive restart and observation backend contracts; separate authorization gates for paid V3 and protected V2 evaluation. **UI remains paused.**
