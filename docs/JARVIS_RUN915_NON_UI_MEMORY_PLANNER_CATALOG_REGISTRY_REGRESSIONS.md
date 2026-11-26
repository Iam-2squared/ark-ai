# ARK AI Run915 — non-UI independent regression hardening

**Source/test work-basis HEAD** `c953610e5c5d52aefa3a89457005711a5969d4be` (Run914). **Complete new test HEAD** `15bee17e7117d4e2e8136aedfb995d64a7157f4b`. All writes were normal GitHub Contents API writes on `research/jarvis-foundations` / Draft PR #8, with a fresh PR HEAD read before each write. Four independent synthetic/non-UI packages, **12 newly authored pytest cases**. This report does **not** claim those cases pass until an exact-HEAD CI matrix certifies them.

## 1 — Memory: multi-row expiry atomicity on fault

[Test source](https://github.com/Iam-2squared/ark-ai/blob/15bee17e7117d4e2e8136aedfb995d64a7157f4b/tests/test_memory_multiscope_expiry_rollback_run915.py) / commit `a654fcf785b15919afa311677c857af99160a073`. Two scenarios (scoped and cross-owner unscoped due-page) inject a failure on the second expire-event insert after the first row event has been staged. An independent Memory reader must still observe both pre-existing rows and original scoped event histories; after fault removal a fresh committed purge must delete the due rows without an event-ID gap while retaining future content. Test-only failure injection; no real private data, physical device or independent audit authority.

## 2 — Planner: terminal fanout / sibling cold recovery

[Test source](https://github.com/Iam-2squared/ark-ai/blob/15bee17e7117d4e2e8136aedfb995d64a7157f4b/tests/test_planner_terminal_fanout_cold_recovery_run915.py) / commit `2841b233a2e2110d4bc9d55486717dc02ae4e8ac`. Two terminal states (FAILED and CANCELLED) in a synthetic DAG, root -> child -> leaf plus independent sibling. Cold recovery must retain terminal BLOCKED descendants, reject stale RUNNING retries for root/children without journal mutation, and leave the independent sibling PENDING until an explicit synthetic append. After the latter, RUNNING remains ambiguous and never authorizes dispatch/replay. This is not real exactly-once effects proof.

## 3 — Memory and Planner: cumulative/UTF-8 SQLite catalog bounds

[Test source](https://github.com/Iam-2squared/ark-ai/blob/15bee17e7117d4e2e8136aedfb995d64a7157f4b/tests/test_sqlite_catalog_cumulative_utf8_run915.py) / commit `249c83532aa58239e3009ad13bd138fa5d4a4a1c`. Four synthetic in-memory cases ensure **aggregate** SQLite `sqlite_master` identity fields are budgeted in **encoded bytes**, not just independently per name or in Unicode codepoints. All DDL remains short; split two-row identifiers or one multibyte identifier exceed the pre-existing fixed budgets (Memory 16,384; Planner 4,096) and are rejected before hydrated catalog comparison. No schema migration or user database alteration; `PRAGMA writable_schema=ON` occurs only in disposable `:memory:` fixtures.

## 4 — ToolRegistry: inert order-invariant binding

[Test source](https://github.com/Iam-2squared/ark-ai/blob/15bee17e7117d4e2e8136aedfb995d64a7157f4b/tests/test_registry_inert_ordered_binding_run915.py) / commit `15bee17e7117d4e2e8136aedfb995d64a7157f4b`. Four tests ensure stable registration revision/bound-action identity independent of registration order, reject reflectively changed registration metadata and mismatched capability, and check that a test backend's `execute` is never invoked during construction/binding. This is registry identity only; it is not permission, real dispatch, or trusted external backend attestation.

## Exact CI provenance at report preparation

- Previous Run914 final HEAD `c953610e...` [#43821247158](https://github.com/Iam-2squared/ark-ai/actions/runs/43821247158): **GREEN 6/6**, Windows and Ubuntu, Python 3.11–3.13. Applies to Run914 only.
- [#43827743869](https://github.com/Iam-2squared/ark-ai/actions/runs/43827743869) `15bee17e7117d4e2e8136aedfb995d64a7157f4b`: **QUEUED**
- [#43827591063](https://github.com/Iam-2squared/ark-ai/actions/runs/43827591063) `249c83532aa58239e3009ad13bd138fa5d4a4a1c`: **IN_PROGRESS**
- [#43827465454](https://github.com/Iam-2squared/ark-ai/actions/runs/43827465454) `2841b233a2e2110d4bc9d55486717dc02ae4e8ac`: **IN_PROGRESS**
- [#43827383025](https://github.com/Iam-2squared/ark-ai/actions/runs/43827383025) `a654fcf785b15919afa311677c857af99160a073`: **IN_PROGRESS**
- The report commit itself triggers another GitHub CI run; a later checkpoint must distinguish its exact HEAD. **Latest Run915 exact-head all-six GREEN not yet established** at the report write.

## Safety and remaining gates

Only new test files and this evidence report were changed. No production source/API contract, frozen V1/V2/Local UI/Launcher evidence, main, protected V3 PR #5, or paused UI PR #9 was edited. PR #5/#8/#9 remain Draft/unmerged. No paid/external GPU or API, training/weights/Candidate generation/promotion, secret/account connection, user-data ingestion, actual tool execution/notification, destructive action, protected evaluation opening, or physical-PC action. No force push, raw Git bypass or manual duplicate CI run.

**Unresolved:** SQLite WAL/SHM process-last-close sidecar alias race remains UNKNOWN/FAIL; independent source/provenance custody and trusted audit clock/real consent remain unproven. Planner cross-store COMMIT-UNKNOWN/effect exactly-once proof and Memory durability under wider inter-process failures are open. The synthetic registry is not a live executor. JARVIS overall **NOT_PASSED**.

**Next plan:** Verify all 6 exact-head CI jobs and repair only genuine regressions; isolate process-last-close WAL/SHM in disposable two-process diagnostics; deepen Planner/Memory persistent invariants and then disconnected registry/gate/audit mock integration after GREEN; continue Personal Context privacy and free V3 guard evidence. Maintain UI PAUSED and all frozen gates.
