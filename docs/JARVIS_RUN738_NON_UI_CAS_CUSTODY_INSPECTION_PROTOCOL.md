# Run738 — Non-UI Memory CAS and detached SQLite/POSIX custody review

## Scope and verified work basis

- **Repository:** `Iam-2squared/ark-ai`, Draft PR #8, branch `research/jarvis-foundations`. Work-basis HEAD was **`e74accab60b1e16bc6011fbf075aa8a89995199d`** (Run737 checkpoint).
- **Previous exact checkpoint CI:** [Run #42611590087](https://github.com/Iam-2squared/ark-ai/actions/runs/42611590087) completed **5/6 GREEN, 1/6 FAIL**: Ubuntu Python 3.13 only. The job log has **11,801 PASS, 1 FAIL, 1 SKIP**. The one failure was `tests/test_memory_cross_process_create_race_run435.py::test_concurrent_memory_initial_create_is_single_cas_per_identity[separate-source-expected3]`: a child process exited *before the simultaneous CAS release gate*, without preserved child stderr in the original assertion. **The cause of that child exit is unproven**; it must not be described as a proven production race. The immediately preceding report-head run [#42611405911](https://github.com/Iam-2squared/ark-ai/actions/runs/42611405911) was six-job GREEN on a *different HEAD*.
- Current work is FREE-ONLY, detached/synthetic, read-only where stated, and does not authorize an actual tool, SQLite repair, user-data disclosure or external GPU.

## Package A: separate cross-process CAS from unrelated startup

- **Commit:** [`0f61258d`](https://github.com/Iam-2squared/ark-ai/commit/0f61258d3260948b8cd6714ea7431231133612c2).
- Startup of the two child `SQLiteMemoryStore` handles is now **serialized and observed** (each child must reach `ready-N` before starting the next). Once both are ready, a single gate still simultaneously releases both independent processes into their `put(..., expected_revision=0)` operations.
- Same-identity create conflict and disjoint owner/namespace/source independence assertions, final row/event counts and identities are **unchanged**. Failure at child bootstrap reports bounded child stderr rather than the opaque "exited before release". Independent multiprocess bootstrap tests remain outside this narrowly scoped CAS test.
- This does *not* claim to resolve an unknown child-bootstrap failure or prove hardware/offline behavior.

## Package B: detached SQLite sidecar preaccess codec/capacity fence

- **Source:** [`21b85cbd`](https://github.com/Iam-2squared/ark-ai/commit/21b85cbd21f3b6b1c19e118b216bedbbe25051da).
- **Tests:** [`450035d8`](https://github.com/Iam-2squared/ark-ai/commit/450035d871fff54fc27fa488773852be0d8c16fc), **20 new parameterized cases** in `tests/test_disconnected_sqlite_sidecar_preaccess_run738.py`.
- `capture_disconnected_sqlite_sidecars`, `review_disconnected_sqlite_sidecars`, `_capture_once` and `_hash` now check their original SHA-256/JSON modules and callable identities, original domain, SHA validator and sidecar suffix set, and exact original path/file byte budgets **before inspecting a path or invoking a digest callback**.
- Synthetic injections cover changed hash/JSON module bindings, hash or JSON callbacks, domain, SHA regex, suffix set and budget values. The test asserts no fixture inspection or attacker-controlled callback was invoked.
- Not an independent security boundary; a hostile in-process writer could mutate code/module state. POSIX-only directory-relative inventory remains unsupported on Windows, deliberately fail-closed.

## Package C: held POSIX fixture descriptor post-named-stat recheck

- **Source:** [`35b2bf3f`](https://github.com/Iam-2squared/ark-ai/commit/35b2bf3f7d8cbf26e8c5e3d5f9e53260d0151c03).
- **Tests:** [`6b1ba2d0`](https://github.com/Iam-2squared/ark-ai/commit/6b1ba2d0558aa973e139ad8b803a04ad3332739d), **4 new cases** in `tests/test_disconnected_posix_handle_poststat_run738.py`.
- After verifying the final named-file stat, the read-only `_once` now rechecks the **held source descriptor** against the metadata that bounded the bytes actually hashed. If a reentrant stat callback modifies the same inode after supplying its pre-change stat result, the inspection fails closed. Three injected changes and one non-mutating control are exercised using disposable files.
- This does not solve general TOCTOU, post-function mutation, Windows pathname custody, SQLite WAL atomicity, source authentication or independent evidence provenance. No real ToolBackend or writable SQLite VFS introduced.

## CI / exact-head evidence

- **Changes saved:** 5 source/test commits; 2 distinct production modules changed, 1 existing cross-process test corrected, 2 new test files added, **24 authored new synthetic parameter-expanded cases**.
- Work-session source/test HEAD: **`6b1ba2d0558aa973e139ad8b803a04ad3332739d`**. This is **not** a six-platform PASS declaration.
- At the last read, source/test run [#42620017951](https://github.com/Iam-2squared/ark-ai/actions/runs/42620017951) was **QUEUED**. Earlier changed-head runs [#42619508590](https://github.com/Iam-2squared/ark-ai/actions/runs/42619508590), [#42619701187](https://github.com/Iam-2squared/ark-ai/actions/runs/42619701187), [#42619811361](https://github.com/Iam-2squared/ark-ai/actions/runs/42619811361) were **IN PROGRESS**. These are independent commit heads; results cannot be inherited by later commits.
- No full local pytest claim: the container has no GitHub DNS for a repository checkout. CI is ordinary GitHub auto-triggered PR verification; **no duplicate manual workflow dispatch**.

## Authorization, freeze and next plan

- Concurrent anchors rechecked: main `7a843f17eb96ed13d66f23b58b06406b3002e405`; Draft PR #5 `805b377697472268db02650a89c7a94b1c5337c8`; paused Draft UI PR #9 `3b49048dd70eebcb6268299b9ecef4e301bbc0fd`. All remain unmerged. Frozen V1/V2/Local UI/Launcher evidence and contracts unchanged. **ARK/JARVIS/V3 NOT_PASSED.**
- No paid API/GPU/compute, Candidate weights, real adapter, protected V2 evaluation, credential/account, actual user sensor, real tool execution, main merge, forced history, unauthorized V3 approval or UI development.
- **Next:** (1) inspect newest source/checkpoint HEAD six-job CI and fix real failing traces without weakening safety; (2) isolate actual cross-process startup cases and preserve stderr if they fail; (3) extend Memory CAS/ABA/COMMIT-UNKNOWN and coherent event/row witnesses; (4) Planner persistent READ and restart-safe terminal states; (5) PermissionGate, immutable registry, occurrence/audit-before-action only through mock executor; (6) separate reviewed Windows/POSIX descriptor-anchored SQLite design. No automatic real-world action authority.
