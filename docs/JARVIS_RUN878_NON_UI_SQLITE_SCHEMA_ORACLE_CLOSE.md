# Run878 — non-UI SQLite schema-oracle connection lifecycle

Observed at (Asia/Tokyo/JST): 2026-11-15T03:48:57.178+09:00. This is an observed wall clock, not a trusted runtime clock, signed provenance, or approval.

**Work basis:** `7a586154607c73c0152329b220ea29de33502ad0` (prior Run877 checkpoint, CI [#43624213673](https://github.com/Iam-2squared/ark-ai/actions/runs/43624213673) GREEN on all six Windows/Ubuntu Python 3.11–3.13 jobs). **Latest complete source+tests HEAD:** `3dd75b947080dda84653869aacd23730cf44facf` (CI [#43628459290](https://github.com/Iam-2squared/ark-ai/actions/runs/43628459290) QUEUED at review; **NOT** yet GREEN). Branch `research/jarvis-foundations`, [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8), no main merge.

## NEW — three independent backend maintenance packages; nine authored regressions

1. **Durable synthetic occurrence schema verification**: `src/ark/agency/durable_occurrence_review.py` now uses `closing(sqlite3.connect(":memory:"))` for the one-table/two-unique-index DDL oracle. This closes its disposable handle on valid schema, same-count wrong schema and exceptions. Source commit `417c68a53bfcfad4702ea6941d5de55eec758ef8`, three synthetic tests `tests/test_occurrence_schema_oracle_close_run878.py` at `2f3ed6be26c094892a927ec9f7af71793081f411`.
2. **Atomic pre-action intent/audit schema verification**: `src/ark/agency/disconnected_atomic_preaction_ledger.py` closes its in-memory oracle on valid comparison, same-count foreign schema and catalog fault. Source commit `11aecb582745ed8bccab5d458870f90eebcc4ace`, three tests `tests/test_atomic_preaction_schema_oracle_close_run878.py` at `74e7c500e4167d0b4c089becb6313342072bdbbd`.
3. **Memory v1 frozen schema verification**: `src/ark/memory/sqlite_store.py` closes only the throwaway in-memory reference DDL connection. The frozen Memory v1 DDL, persistent connection semantics, CAS and event rules are untouched. Source commit `a966e9e2a07bbe9e325f3a342bd93d6d8e94bc3a`, three tests `tests/test_memory_schema_oracle_close_run878.py` at `3dd75b947080dda84653869aacd23730cf44facf`.

**Why:** A Python SQLite connection's context manager commits/rolls back but **does not close the connection**. For disposable schema references, explicit `closing(...)` is necessary. Each regression asserts that the actual temporary connection rejects a query after its verifier finishes, including failure paths. Tests use only synthetic local `:memory:` schemas and injected failures; they do not dispatch tools or change stored data.

[Exact source/test diff](https://github.com/Iam-2squared/ark-ai/compare/7a586154607c73c0152329b220ea29de33502ad0...3dd75b947080dda84653869aacd23730cf44facf) contains **exactly three backend source files and three added test files** (six commits, three cases per test file). No frontend/UI, frozen contract, existing test, schema DDL, protected V2 evaluation or V3 Candidate asset is modified.

## CI / test evidence and limitations

- Previous exact-head Run877 [#43624213673](https://github.com/Iam-2squared/ark-ai/actions/runs/43624213673): six jobs **GREEN** (not proof for Run878).
- First occurrence source and test [#43628173809](https://github.com/Iam-2squared/ark-ai/actions/runs/43628173809) and [#43628244398](https://github.com/Iam-2squared/ark-ai/actions/runs/43628244398): IN PROGRESS on most recent Actions listing.
- Atomic source and tests [#43628266863](https://github.com/Iam-2squared/ark-ai/actions/runs/43628266863), [#43628354892](https://github.com/Iam-2squared/ark-ai/actions/runs/43628354892): IN PROGRESS / QUEUED.
- Memory source and tests [#43628422369](https://github.com/Iam-2squared/ark-ai/actions/runs/43628422369), **latest full source+test** [#43628459290](https://github.com/Iam-2squared/ark-ai/actions/runs/43628459290): QUEUED. Nine cases are **authored**, not proven PASS. Do not back-project an older GREEN onto the newest HEAD.
- No physical target-PC/GGUF validation, local clone/pytest/Ruff or paid compute: container could not resolve github.com. Writes used the permitted GitHub Contents API with fresh PR HEAD and per-file blob SHA, never raw Git tree/ref operations, force pushes or main merge.

## Independent read-only incident review

Historical [#43596487033](https://github.com/Iam-2squared/ark-ai/actions/runs/43596487033) logs confirm an Ubuntu Python 3.13 Privacy Revocation contender lost for a reason **other than** the expected `already revoked`, and a Windows Python 3.11 Memory process saw a transient `-wal` file with `st_nlink == 0`. Both remain open diagnostic questions, **not** fixed by this connection-lifetime maintenance. Preserve strict sidecar identity checks, no automatic retry after COMMIT uncertainty, and the exact-type privacy veto. No speculative assertion that the SQLite fixes cure cross-process races.

## Blockers / approval gates

Frozen V1/V2/Local UI/Launcher contracts and evidence unchanged; [Draft PR #5](https://github.com/Iam-2squared/ark-ai/pull/5) and paused [Draft UI PR #9](https://github.com/Iam-2squared/ark-ai/pull/9) untouched, unmerged. No new UI work, paid API/external compute, credentials, real Candidate training or promotion, protected evaluation, physical-PC operation, real executor, destructive migration or approval-gated merge. These synthetic connections do not establish trusted identity, human consent, independent custody, external exactly-once effects or whole-system PASS.

## Next plan / 今後の方針

1. Verify exact latest source+test CI all six environments; fix any real failure with the smallest safe normal Contents API edit and fresh-head reconciliation.
2. Investigate Privacy Revocation loser classification, transient Windows `-wal` last-close `st_nlink=0`, Memory/ActionAudit COMMIT-UNKNOWN without weakening denial or automatic replay.
3. Advance Memory CAS/expiry/coherent snapshots and Planner RUNNING→UNKNOWN recovery using independently retained witnesses and synthetic failure injection.
4. Connect registry-bound ToolRegistry, exact-type PermissionGate, durable occurrence fences and audit-before-action to a disconnected Mock Executor only after lower-layer exact-head GREEN.
5. Continue privacy-safe Personal Context/proactive/observation fixture contracts and V3 free-only guards. UI remains paused; no later PASS inference.
