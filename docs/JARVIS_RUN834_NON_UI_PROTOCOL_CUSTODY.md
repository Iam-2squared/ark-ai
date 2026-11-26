# ARK AI Run834 — non-UI in-process descriptor custody and privacy inventory

**Scope:** isolated, reversible, free-only backend foundations on Draft PR #8 `research/jarvis-foundations`. **Overall ARK/JARVIS NOT_PASSED**. Source is not a security sandbox; locally pinned original objects do not authenticate a device, approval, actual deletion, physical-time claim or remote executor.

## Initial basis / concurrency

- Initial verified PR/branch HEAD: `c78df2fb5a5bbeb96a3c19369b01b06e0fb0ad77` (the preceding six Run833 source/test commits; their latest CI was not GREEN yet at the first read).
- Baseline Run832 checkpoint: `7aafb13d61bee7a3a225f9855a734dd81600671d`, CI [#43348129610](https://github.com/Iam-2squared/ark-ai/actions/runs/43348129610) **GREEN 6/6**. Do **not** use this older green as proof of newer source.
- PR #5 remains a protected Draft and PR #9 remains UI-paused Draft; no changes to either. Current changes are confined to three non-UI source files and three new tests. Each Contents API write was preceded by a live PR HEAD re-read. No ref rewrite, duplicate workflow dispatch, protected evaluation or source-to-main merge.

## New package 1 — proactive startup source identity

- [Source `05fadb38`](https://github.com/Iam-2squared/ark-ai/commit/05fadb38a0f6ea348b06ba75746d52220d5b10c9), [8 authored tests `4e8b4974`](https://github.com/Iam-2squared/ark-ai/commit/4e8b4974f869e4195e9b0b560f3045294cd19ad2).
- `_require_original_authorities()` previously used Python tuple value comparison for six source classes and their descriptors, potentially invoking caller-installed `__eq__` or `__ne__` before startup/readiness validation. It now checks exact import-time class and descriptor identities with `is not`.
- Tests cover untouched original protocol, poisoned metaclass equality, and all six source descriptor positions. The fixture remains deny-only: no READY attestation, notification, ToolBackend dispatch, or automatic replay.

## New package 2 — detached PNG inventory format custody

- [Source `9aafe8bd`](https://github.com/Iam-2squared/ark-ai/commit/9aafe8bd85562386a3933991f0e61fc677c60d27), [8 authored tests `7a37e235`](https://github.com/Iam-2squared/ark-ai/commit/7a37e2356764f74297d736cfbda6d0c1eaca70f1).
- The original `tuple(sorted(_VALID_DEPTHS.items())) != _ORIGINAL_VALID_DEPTHS` could execute a replaced depth value's Python equality method *before inspecting private PNG bytes*. The guard now requires a plain dict with integer keys, the original five keys and original depth-tuple objects, without executing attacker-supplied comparison or iteration.
- Cases include all five color-type entries, equal-value fresh tuple, extra noninteger key and untouched metadata-only PNG success. No pixel decoding, camera access, consent inference, source authentication or private content export.

## New package 3 — privacy-safe retained Memory inventory items

- [Source `19228383`](https://github.com/Iam-2squared/ark-ai/commit/1922838350a44d7b160ac17d2c7ebee79489fe76), [6 authored tests `f2936862`](https://github.com/Iam-2squared/ark-ai/commit/f293686279159cfca340fbf6e89a5dea3c867fe3).
- Replaces retained-item tuple value equality with an import-original, exact-identity helper for `memory_id`, `revision`, and `RetentionState` across independent Memory and revocation reads. Reflection-poisoned members cannot invoke `__eq__`/`__ne__` and value-equal replacement is not accepted as the same local epoch.
- Cases cover unchanged DTO, all three poisoned members, cloned-equal ID and foreign item getter. No private row serialization in tests, deletion, erasure attestation or automatic context release.

## CI and boundaries

- The six new commits generate six **automatic** pull-request CI runs, not manually duplicated workflows: [#43355507498](https://github.com/Iam-2squared/ark-ai/actions/runs/43355507498), [#43355661898](https://github.com/Iam-2squared/ark-ai/actions/runs/43355661898), [#43355895435](https://github.com/Iam-2squared/ark-ai/actions/runs/43355895435), [#43355956441](https://github.com/Iam-2squared/ark-ai/actions/runs/43355956441), [#43356134818](https://github.com/Iam-2squared/ark-ai/actions/runs/43356134818), [#43356201522](https://github.com/Iam-2squared/ark-ai/actions/runs/43356201522). At the last read, all were **QUEUED** except source #43355507498 **IN_PROGRESS**. The final checkpoint commit creates its own further CI.
- **22 tests authored, not 22 verified PASS. Final HEAD 6/6 CI GREEN NOT ESTABLISHED.** No full local pytest/Ruff, Windows physical host, or GGUF model runs performed.
- Previous WAL/SHM zero-link race diagnosis remains unresolved. Never weaken link/symlink/sidecar safety checks to make tests pass. Neither diagnostics nor hashes prove independent custody or exactly-once external effects.
- No frontend/UI, frozen V1/V2/Local UI/Launcher contracts, paid compute, new credentials, GPU, Candidate/weights generation or promotion, V2 final protected evaluation, real tool dispatch, destructive operation or main merge.

## Next

1. Inspect exact-head CI/jobs for these code and test commits. Fix any real source/test failure via normal Contents API only, preserving denial semantics, while auditing independent modules during CI.
2. Continue Memory WAL/SHM race isolation on disposable SQLite only; COMMIT-UNKNOWN manual reconciliation, CAS and coherent expiry without automatic retry.
3. Advance Planner persisted UNKNOWN and terminal propagation; then exact ToolRegistry/PermissionGate, trusted-clock audit-before-action and inert Mock Executor after dependency-head CI GREEN.
4. Continue privacy revocation/retention, proactive occurrence/restart, observation fixtures and V3 detached free-only guards. Do not resume UI or open protected gates without explicit user permission.
