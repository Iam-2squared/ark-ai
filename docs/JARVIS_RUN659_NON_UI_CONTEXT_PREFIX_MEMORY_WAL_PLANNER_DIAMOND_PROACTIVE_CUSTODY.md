# ARK AI — Run659 non-UI core: Context prefix, Memory WAL, Planner recovery and proactive guard

## Scope and work-basis

- Working branch: `research/jarvis-foundations`, [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8), isolated from main and all frozen V1/V2/Local UI/Launcher evidence.
- Verified initial work-basis HEAD: `f16be360a68928fd682c9119b4d2e6cd6bc40239`, with [GitHub Actions #42198638663](https://github.com/Iam-2squared/ark-ai/actions/runs/42198638663) completed SUCCESS / Ubuntu+Windows Python 3.11–3.13 all six jobs.
- UI/front-end work remains paused; PR #9 remains Draft/unmerged and untouched. V3 PR #5 remains Draft/unmerged; no protected evaluation or paid-compute gates were opened.

## Four independent non-UI work packages

1. **Personal Context retained-prefix result custody.** `src/ark/personal_context_replay_prefix_review.py` now captures and verifies import-original `OfflineContextPrefixReview` slotted value descriptors, initializer, allocation and lookup hooks in addition to denial-only getters. It rejects replaced executable result members **before accessing result fields or constructing a result**, including after reentrant digest callbacks. `tests/test_context_prefix_original_result_carriers_run659.py` contains **12 authored cases** for preinstalled slots, hash/digest reentry, child-process-isolated inherited allocation poison, and an inert healthy control. Evidence remains a local synthetic prefix, never consent or authenticated provenance.

2. **Memory WAL prefix snapshot / append-only history.** `tests/test_memory_prefix_wal_and_truncation_run659.py` contains **6 authored cases**. A separate SQLiteMemoryStore writer commits CREATE, UPDATE or DELETE while a reader is already charging the first event into a retained prefix; the running scan must retain one WAL snapshot, while a fresh scan and comparison observe the suffix as unauthenticated. Separate first/middle/tail event-loss regressions require both event alignment and event-prefix audits to refuse corrupted disposable fixture histories. No physical deletion, external action, or independently verified writer is claimed.

3. **Planner diamond restart and mixed recovery fence.** `tests/test_planner_diamond_mixed_fence_run659.py` contains **3 authored cases**. Two SQLite journal handles commit independent branch transitions; a FAILED/CANCELLED WRITE root blocks the join despite an independent successful READ, while unresolved RUNNING roots quarantine the WRITE and its descendant without blocking independent mock-only READ readiness. Journal-to-fence state projection is deliberately manual and unauthenticated, never dispatch permission.

4. **Proactive recurrence carrier integrity.** `src/ark/disconnected_schedule_preview.py` pins import-original input policy, cursor and output preview slotted descriptors plus constructor/allocation/getter hooks, refusing replaced executable class members prior to reading schedule metadata or hashing an occurrence. `tests/test_schedule_preview_original_carrier_slots_run659.py` contains **16 authored cases**, including preinstalled fields, reentrant hash mutation, subprocess-isolated allocation poisoning, and inert healthy preview. Caller clocks remain untrusted; no OS timer, notification, automatic replay, or tool backend is used.

**Total: 37 authored new parameterized test cases, NOT a claim of 37 measured passes.** The four packages do not modify source contracts or schema version, and do not integrate a real executor.

## CI and verification record

- Baseline [#42198638663](https://github.com/Iam-2squared/ark-ai/actions/runs/42198638663): six-job GREEN on exact initial work-basis HEAD.
- Context source [#42205361394](https://github.com/Iam-2squared/ark-ai/actions/runs/42205361394): all three Ubuntu jobs GREEN at initial review; Windows was running. Do not extrapolate its result to later commits.
- Memory regression [#42205510623](https://github.com/Iam-2squared/ark-ai/actions/runs/42205510623): all three Ubuntu jobs GREEN at initial review; Windows was running.
- Planner test [#42205699365](https://github.com/Iam-2squared/ark-ai/actions/runs/42205699365): all six jobs FAIL on Ruff `I001`, **not** on functional assertions. The imports were reformatted in `e80d682a706ff38c1720b1b97a8e8674f44185ac`; core source semantics were unchanged.
- Earlier overlapping runs [#42205958834](https://github.com/Iam-2squared/ark-ai/actions/runs/42205958834), [#42206169037](https://github.com/Iam-2squared/ark-ai/actions/runs/42206169037), and [#42206333083](https://github.com/Iam-2squared/ark-ai/actions/runs/42206333083) failed while the same unformatted Planner import was still present. The later fixed-head matrix [#42206468792](https://github.com/Iam-2squared/ark-ai/actions/runs/42206468792) was **IN PROGRESS** at the first status check.
- No duplicate workflow was manually launched. No local clone/full test run was performed because public GitHub DNS resolution is unavailable in the container. The final exact-head CI result must be separately checked; an earlier GREEN is never a substitute.

## Invariants, restrictions and next validation

- All new tests use disposable, synthetic data; hashes and SQLite read transactions are local diagnostics only.
- No paid/external GPU, billable API/service, new account/credential, actual sensor/hardware, Candidate adapter or training run, real tool backend dispatch, protected V2 evaluation opening, approval promotion, destructive production operation or main merge.
- The Memory WAL snapshot has no independently authenticated source; the Planner recovered RUNNING state is ambiguous and never auto-replayed. The Context and schedule guards do not turn in-process Python code into a security sandbox.
- Next: confirm all six exact-head CI jobs. On failure inspect the failed job logs and apply a narrowly scoped, semantics-preserving correction via the normal GitHub Contents API. Thereafter prioritize retained Memory prefix/COMMIT-UNKNOWN, Planner audit-before-action and reservation integrity, and privacy-safe proactive/Context recovery. Maintain the UI pause and frozen-evidence boundaries.
