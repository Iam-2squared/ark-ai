# ARK AI Run977 — disconnected Personal Context replay and READ journal hash-chain custody

Read-only evidence and non-UI implementation report. Generated 2026-11-18T21:50:38.162Z UTC (reporting time only, not an authoritative timestamp).

## Scope and work basis

- Repo: `Iam-2squared/ark-ai`; Draft PR #8 / `research/jarvis-foundations`.
- Initial exact HEAD: `3db9f4f2fc1fb9a126b5d428801f2255af88b1b9`, [Run976 CI #44397552241](https://github.com/Iam-2squared/ark-ai/actions/runs/44397552241) 6/6 SUCCESS.
- No UI, frontend, frozen-contract, V3 final evaluation, Candidate, live tool backend, main merge or protected PR #5/#9 changes.
- No paid compute, API, new service/credential, physical device, destructive migration or replay of ambiguous effects.

## Work package A: Personal Context synthetic replay ledger

- Source commit [`73c48b4df`](https://github.com/Iam-2squared/ark-ai/commit/73c48b4df169b786a46dc1037c4541f12660a8fc); test commit [`60cc19b8c`](https://github.com/Iam-2squared/ark-ai/commit/60cc19b8c9639fcec8be78770dc3ad6d2d7d4485).
- `src/ark/personal_context_replay_ledger.py`: import-time custody of JSON serializer, SHA-256 callback, digest domain, regular-expression identity admissions, schema DDL, row capacity and dependent module identity. Fail-closed guard before path inspection, witness/binding field access, SQL schema review and hashing. Recheck between JSON serialization and SHA-256 invocation and afterward.
- New `tests/test_context_replay_protocol_custody_run977.py`: **17 synthetic cases** cover changed SHA/JSON callbacks across create/restart/witness/prefix/genesis, mutated protocol constants/budgets and valid cold-read prefix. Private callable injection checks that callback receives **zero** caller metadata and rejected create does not create a file.
- Boundaries: this only guards mutation of Python references during a process. A genuine independently held witness, user consent, private-data erasure, trusted expiry time and external replay authority remain unproven. Existing frozen Memory v1 and Personal Context opt-in fixture semantics unchanged.

## Work package B: detached READ journal

- Source commit [`904546b9f`](https://github.com/Iam-2squared/ark-ai/commit/904546b9f53d0d38934c11f8bf3c6bd566e545c5); tests commit [`1351f3df`](https://github.com/Iam-2squared/ark-ai/commit/1351f3df786506e9122029828cb97b1931b4982e).
- `src/ark/agency/disconnected_read_journal.py`: import-time custody of deterministic chain rules (SHA-256, JSON encoding, domain, genesis, exact regexes, operation allowlist, SQLite schema marker/DDL and row budget). Guard path admission before touching a ledger; check exact protocol before receipts, witness, persisted schema, and each hash step.
- New `tests/test_read_journal_protocol_preaccess_run977.py`: **22 synthetic cases** exercise callback replacement across create/open/verify/recovery/append/genesis, static format mutation and the unmodified append/restart/recovery deny-only path.
- Boundaries: READ journal rows and retained tips are locally derived, not proof that a model executed, a ToolRegistry action was authorized, or any real tool/side effect happened. No automatic replay or READ dispatch was added.

## Independent Memory WAL/SHM inspection (read-only)

- Examined `src/ark/memory/sqlite_store.py` `_require_safe_memory_path` and first-open `_BOOTSTRAP_LOCK`, plus `test_ark_wal_sidecar_lifecycle_fence_run923.py` and `test_ark_wal_cold_restart_phases_run913.py`.
- Implemented guards reject alias/special-file sidecars, journal-suffix native-byte path overflow and known orphan sidecars. The shared `RLock` serializes **same-process** initializations only. The code documents lstat race windows and does **not** establish cross-process path custody, independent writer identity, or database+external-effect atomicity.
- Next safe advancement: isolated deterministic multi-process WAL/SHM fault fixtures and post-open path/handle identity review, with explicit Windows vs POSIX behavior and rollback/COMMIT-UNKNOWN quarantine. No live PC or final evaluation attempted in this run.

## Exact-head CI: latest observed

- [#44405217019](https://github.com/Iam-2squared/ark-ai/actions/runs/44405217019): `1351f3df786506e9122029828cb97b1931b4982e` — QUEUED (at reporting read).
- [#44405133171](https://github.com/Iam-2squared/ark-ai/actions/runs/44405133171): `904546b9f53d0d38934c11f8bf3c6bd566e545c5` — IN_PROGRESS (at reporting read).
- [#44404855612](https://github.com/Iam-2squared/ark-ai/actions/runs/44404855612): `60cc19b8c9639fcec8be78770dc3ad6d2d7d4485` — IN_PROGRESS (at reporting read).
- [#44404755907](https://github.com/Iam-2squared/ark-ai/actions/runs/44404755907): `73c48b4df169b786a46dc1037c4541f12660a8fc` — IN_PROGRESS (at reporting read).

These are authored tests committed to the branch, **not** a declaration that the final source/test HEAD is GREEN. The previous Run976 exact HEAD was GREEN. CI may still be queued/in progress; inspect job logs for failures and fix by the normal file-write path only. No duplicate manually dispatched workflow run.

## Safety and integration gates

- `Memory v1`, `PlanStep/ToolCall v1`, `Observation Envelope v1`, frozen V1/V2/Local UI/Launcher and gated V3 evaluation unchanged.
- PR #5 Draft/gated/unmerged; PR #8 Draft/unmerged; PR #9 Draft, UI paused/unmerged.
- No paid/external compute, credentials, automatic authorization or synthetic-to-production executor bridge.
- Unresolved: independent storage custody, consent/trusted-clock attestation, cross-store crash coordination and physical-device proof.
- Prioritize (1) exact-head CI diagnosis, (2) Memory WAL/SHM and generation CAS recovery, (3) Planner terminal persistence/one-shot authorization/audit-before-action on disconnected mocks, (4) Personal Context revocation/reuse and proactive occurrence review, (5) zero-cost V3 guards without touching frozen approval/evaluation.

**Overall JARVIS: NOT_PASSED.**
