# ARK AI — Run701 non-UI core safeguards / 2026-11-08 JST

> **DRAFT / NOT_PASSED.** FREE-ONLY, disconnected/mock-only code and disposable SQLite fixtures. No paid compute, model/Candidate generation, protected V2 final evaluation, real tool dispatch, new credentials, physical-PC action, UI/frontend work or main merge.

## Exact starting point and scope

- Repository: `Iam-2squared/ark-ai`, `research/jarvis-foundations`, Draft PR #8 (unmerged).
- Initial work-basis HEAD: `c6446443a5b3267703efa8994324a5e593ebc569` (Run700 checkpoint).
- All writes use ordinary GitHub Contents APIs with fresh branch HEAD reads and current file blob SHAs. No force push or raw Git object/update-ref bypass.
- Frozen V1/V2/Local UI/Launcher evidence and contracts unchanged. Draft PR #5 remains independent and protected; Draft PR #9 remains paused and untouched.
- Changes: **four packages**, three production modules, one corrected existing test file plus three new dedicated test files, and an additional legacy test diagnostic adjustment. **29 new test cases authored (7 Memory, 14 Planner, 8 Observation).** These are authored cases, not a claim of all-platform PASS.

## A — CI failure: CPython inherited `__new__` slot

- Starting exact HEAD [CI #42436663480](https://github.com/Iam-2squared/ark-ai/actions/runs/42436663480) completed with pytest failure on all platforms. Ubuntu 3.12 actual log: 2 FAIL, 10,816 PASS, 1 SKIP; `test_unmodified_receipt_still_denies_dispatch` and `test_stable_retained_history_never_grants_dispatch` raised `TypeError: object.__new__() takes exactly one argument`.
- Root cause: a test patched the **original slotted dataclass class** `__new__`, and deleting that inherited attribute after test did not recover the CPython type allocation slot. Subsequent good-path constructors were poisoned, even though `vars(cls)` appeared restored. Reproduced locally with a minimal slotted dataclass.
- Normal test-only commit `d54599be86df6f53a26c56648a21bc24d2fea99c`: seven original-carrier field/lookup cases stay in-process; the direct hostile `__new__` test runs in a separate local Python subprocess, testing early denial and zero malicious callbacks without poisoning the main pytest worker. Production refusal unchanged.
- Corrected source/test exact-head [CI #42440043098](https://github.com/Iam-2squared/ark-ai/actions/runs/42440043098) showed Ubuntu 3/3 GREEN and Windows 3 IN PROGRESS on first post-fix read; do not call 6/6 GREEN until separately verified.

## B — Memory atomic WAL snapshot: cross-scope global append high-water

- `src/ark/memory/atomic_epoch_review.py` source commit `56404efe477c47d55f1df38a90b90d8e4f2bf892` adds one read-only global `COUNT/MIN/MAX(event_id)` plus `sqlite_sequence` check inside the **existing anchored SQLite read transaction**, before the caller clock callback and before owner-filtered row/event projections. The frozen v1 schema, event write APIs and report fields are not changed.
- This prevents a locally consistent same-owner partial graph from overlooking a deleted foreign-owner/terminal event or an altered global sequence. It detects local journal inconsistency, not historical authorship, authenticated provenance, consent, or full physical erasure.
- `tests/test_memory_atomic_global_append_highwater_run701.py` new tests committed at `e3284efb4b6142fd6c1d22d7341b271faef5671e`: 7 fixtures cover first/middle/last foreign event removal (3), missing foreign event with coherent own history, sequence forgery, intact foreign append with no privilege, and a foreign append during the clock callback without mixing WAL epochs.
- [CI #42440134577](https://github.com/Iam-2squared/ark-ai/actions/runs/42440134577) found **one actual pre-existing diagnostic mismatch** at Ubuntu Python 3.11: the deleted-event case in `test_memory_event_causality_run479.py` now fails earlier with `Memory epoch global event high-water mismatch`, not its former late `event lifecycle|live rows` diagnostic. Normal test-only commit `280488e7b4679ed4b21127fe2b523a916a00d3b5` admits the stronger earlier denial; no production rule is relaxed. The repaired HEAD requires a fresh all-platform CI verdict.

## C — Planner detached READ output identity preflight

- `src/ark/agency/disconnected_read_recovery_schedule.py` source commit `6e909b9b63f11e2eae6e9c7b9bc91e937a101c5a` now pins the original two decision field descriptors, three schedule descriptors and each result type's `__new__`, `__getattribute__`, `__getattr__` hooks. Checks occur before reading synthetic graph slots, before each result constructor and after digest callbacks. Previous `__init__`, step-carrier and deny-only flags remain enforced.
- `tests/test_detached_read_recovery_result_descriptors_run701.py` at `8cb860316207f40dee86cedea420fab7bfeae5d8` adds **14** cases: 9 preinstalled field/hook substitutions, two isolated-interpreter `__new__` substitutions (avoiding the CPython trap above), two digest-reentrant substitutions, and one unchanged no-dispatch baseline.
- No planner recovery history is treated as authenticated tool execution or automatic replay permission. No live backend connection is created.

## D — Observation raw-byte SHA handoff

- `src/ark/observation_fixture_adapters.py` source commit `892496d6b8a8cde0b2b5c6f534f7d9791f4091e4` uses its import-pinned original SHA-256 callable, with identity checks immediately before and after hashing caller-private fixture bytes. A substituted callback installed **after** metadata preflight cannot receive those bytes through the fixture adapter's hash handoff.
- `tests/test_observation_fixture_digest_handoff_run701.py` at `ad721fbedef3770e71506f9fe874114417807b97` adds **8** cases: one attempted post-preflight SHA interception for each TEXT/TRANSCRIPT/IMAGE/SCREEN kind, and four valid exact content-hash/non-authority baselines.
- Inputs remain caller-provided in-memory synthetic fixtures, not device, microphone, camera or screen acquisition. In-process import-pinning is not process isolation or external source authentication.

## Evidence classification and limitations

- Existing exact-head failures are not replaced by optimistic assumptions. CI runs [#42440043098](https://github.com/Iam-2squared/ark-ai/actions/runs/42440043098), [#42440134577](https://github.com/Iam-2squared/ark-ai/actions/runs/42440134577), [#42440229776](https://github.com/Iam-2squared/ark-ai/actions/runs/42440229776) refer to distinct test/source HEADs. The final report/checkpoint HEAD runs must be independently reviewed; prior Ubuntu-only success is not final 6/6 evidence.
- The owner/scope identities, SHA-256 digests, SQLite WAL snapshot and caller-supplied times remain synthetic, local and unauthenticated; no exactly-once external effects, authenticated clocks, legal erasure, consent, or permission to dispatch are established.
- No V3 authorizations, real model weights, protected V2 scorer or frozen Contract paths are opened. PR #5/#8/#9 remain Draft/unmerged and UI paused.

## Next plan / 今後の方針

1. Re-read current PR #8 HEAD and CI for Windows/Ubuntu × Python 3.11–3.13; repair any actual failures with minimal semantics-preserving changes and overlap on a different lane.
2. Extend Memory CAS/ABA/COMMIT-UNKNOWN and TTL/WAL retained privacy veto consistency; do not automatically retry ambiguous commits.
3. After exact-head GREEN, proceed with Planner durable per-step READ proofs, UNKNOWN recovery, immutable registry/exact-type permission boundary and restart-safe trusted-clock audit-before-action, **mock-only**.
4. Keep Personal Context minimization/privacy lifecycle, proactive scheduler and observation fixtures moving on isolated non-UI lanes; audit V3 free-only approval/path/reproducibility without authorizing GPU, Candidate, evaluation or main merge.
