# Run895 — non-UI durable-veto DDL custody, Planner diamond, Memory expiry, proactive no-replay

Work-basis: `26f47891872dafd2d5bd4c877358c63ec6049c18` (Run894 checkpoint, CI [#43706172082](https://github.com/Iam-2squared/ark-ai/actions/runs/43706172082), all six Windows/Ubuntu × Python 3.11–3.13 GREEN, checked individually). Source/test result before this report: `0150ec8337e24cbe5351e11af6d7dbb158a457fa`. All development stays on [Draft PR #8](https://github.com/Iam-2squared/ark-ai/pull/8), independent of main, Draft PR #5 and paused Draft UI PR #9.

## NEW packages (five coherent non-UI writes; 13 authored regressions)

1. **Independent privacy diagnostic DDL verification** — source `scripts/diagnose_revocation_wal_processes.py`, commit `f160cdda242d9add048b7b95fed1ad79c3b882e2`. Previously `_verify_row` checked schema-version, the single synthetic revocation row, object *names/types*, and SQLite quick-check but **not the actual SQL table constraints**. A database with the same autoindex/table names but missing `NOT NULL` constraints could have been incorrectly reported as a durable matching fixture. The verifier now compares the exact `sqlite_master.sql` DDL against a separate static diagnostic v1 oracle, without weakening the real ledger's checks. The diagnostic is still disposable, read-only and not authenticated consent, real privacy data or an authorization source.
2. **Planner shared-descendant diamond / fan-in** — `tests/test_planner_terminal_diamond_run895.py`, commit `d425c895c25d06093ddfd8a72970794786fb89d9`; **4 regression cases** across FAILED/CANCELLED cascades, READY fan-in and independently unaffected steps. Distinguishes terminal propagation (one BLOCKED revision per reachable pending descendant) from actual tool execution. Existing frozen contract and Planner source unchanged.
3. **Memory multi-scope expiry across independent interpreters** — `tests/test_memory_multiscope_expiry_process_run895.py`, commit `c84eb99c609ab97fc5f2d8a9bdda192d5a1ed0c8`; **2 authored cases**, disposable SQLite. A scope-only purge leaves a separate expired scope intact until global purge. A child-process CAS refresh in one namespace survives global expiry purge of the other. Global events are expected to remain dense with per-scope event IDs `[1,3]` and `[2,4]`. No DDL change or private context.
4. **Proactive grace-edge / restart no replay** — `tests/test_schedule_grace_restart_no_replay_run895.py`, commit `71a6267071cae65d0070a35840ed40fd18ea200e`; **3 authored cases**. `NOT_DUE` / `DUE_UNVERIFIED` / `EXPIRED_QUARANTINE` around grace boundary, same next occurrence on synthetic restart, and an explicitly advanced-but-unauthenticated cursor. All five execution/notification/consent/trusted-clock/replay properties stay False. No OS clock, timer or notification.
5. **Independent DDL downgrade regression** — `tests/test_revocation_wal_ddl_oracle_run895.py`, commit `0150ec8337e24cbe5351e11af6d7dbb158a457fa`; **4 authored cases**. Three SQLite variants deliberately retain the same `sqlite_master` type/name/table name and the expected single row while weakening `NOT NULL` or changing a `CHECK` constraint. They must now be refused. The canonical real synthetic-v1 fixture must still verify.

No tests or CI verification in this report should be interpreted as real model inference, Windows physical-PC GGUF gate, authorized tool execution, trusted clock, independent human approval or privacy consent.

## CI pipeline evidence (sampled; later commits need their own GREEN)

- **Baseline:** [#43706172082](https://github.com/Iam-2squared/ark-ai/actions/runs/43706172082) — `26f47891...`, **GREEN all six**.
- **Privacy source:** [#43710841179](https://github.com/Iam-2squared/ark-ai/actions/runs/43710841179) — `f160cdda...`, last sampled **IN PROGRESS**.
- **Planner:** [#43710927177](https://github.com/Iam-2squared/ark-ai/actions/runs/43710927177) — `d425c895...`, last sampled **IN PROGRESS**.
- **Memory:** [#43711035541](https://github.com/Iam-2squared/ark-ai/actions/runs/43711035541) — `c84eb99c...`, last sampled **IN PROGRESS**.
- **Proactive:** [#43711147851](https://github.com/Iam-2squared/ark-ai/actions/runs/43711147851) — `71a62670...`, last sampled **QUEUED**.
- **Complete source/test HEAD:** [#43711210075](https://github.com/Iam-2squared/ark-ai/actions/runs/43711210075) — `0150ec83...`, last sampled **QUEUED**.
- An automatic PR CI is triggered after this report and the final PROJECT_STATUS checkpoint; their IDs are not known at the time these files are authored. Do not transfer earlier GREEN.

## Preserved boundaries and unresolved issues

Frozen V1/V2/Local UI/Launcher contracts/evidence, Memory v1 schema and direct Observation v1 semantics remain unchanged; protected V2 final evaluation and V3 authorization/Candidate/reproducibility gates stay closed. PR #5 remains Draft/unmerged; PR #9 remains Draft/unmerged and **untouched**. No UI/frontend changes, real tools, personal data, payments, external paid GPU/API, Candidate training/weights/promotion, credentials, hardware actions, destructive operations or main merges.

The schema-DLL oracle closes only the diagnostic's same-name/different-DDL false-positive; it is **not** a proof of path/inode custody, historical source identity or independent trust. Windows SQLite WAL/SHM last-close race and losing process rejection despite a durable winner remain unresolved. Cross-store COMMIT-UNKNOWN, durable exactly-once action authority, independent privacy authorization and a trusted clock remain blocked.

## Next plan / 今後の方針

1. Confirm all six matrix jobs for the exact latest source/test and checkpoint heads; correct failure without changing semantic fences. Do not launch duplicate CI.
2. Investigate WAL/SHM last-close with bounded, synthetic, phase-correlated observations, keeping all sidecar alias refusals.
3. Advance Planner journal UNKNOWN recovery and Memory CAS/expiry/coherent snapshots in isolated, reversible parts.
4. Prove immutable ToolRegistry/PermissionGate, durable audit-before-action and disconnected mock READ integration against exact-head GREEN before cross-component connection.
5. Continue Personal Context privacy, proactive/observation back-end fixtures and detached zero-cost V3 guards. No UI/frontend lane until explicit user resumption.
