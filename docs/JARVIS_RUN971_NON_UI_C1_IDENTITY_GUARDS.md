# ARK AI Run971 — Non-UI C1 identity admission across four disconnected core boundaries

**Scope:** local-first, non-UI, no backend dispatch. **Work-basis HEAD:** `8eeedfbc571231db4e6805760cf482e0e1401be0` (Run970 checkpoint). This is a technical change record, not a PASS or training claim.

## Problem

In four optional/disconnected admission paths, ASCII C0, DEL and selected Unicode format controls were rejected, but most Unicode **C1 control codes U+0080–U+009F** could still enter identifiers. In particular U+009B is historically a terminal control introducer. Their presence can make diagnostics/log identities ambiguous even when underlying UTF-8 hashes differ. The mitigation applies **only** to the optional boundaries below; it does not silently change frozen public input contracts.

## NEW work saved this invocation

| Independent package | Source commit | Test commit | New parametrized test cases | Behavior |
| --- | --- | --- | ---: | --- |
| ToolRegistry / PermissionGate integration | `bc8b009171fbc00dcca236fe1ab16655721debae` | `e8cf0b796b63e113156b3793e7b8ad765a43ce54` | 33 | Bound registration name/capability/backend identity and `resolve`/`bind` scope all reject C1; registered WRITE rejection does not consume a valid unrelated in-memory one-shot; no backend call |
| Observation fixture adapter | `229fd039c656c5816edbb9c4aecb0120c47b7711` | `bd285bc740d60011327ea6f72f4a565c3a8590e6` | 14 | Synthetic source/privacy C1 labels rejected before fixture hashing; direct frozen Envelope v1 untouched |
| Memory lifetime diagnostic | `9d50f2b0a148dff1e65ea3af2506c5713ae83fb9` | `6b223100aa7d73b8dcce6fd5c467bde522814f53` | 19 | Optional read-only ABA/generation reviewer rejects reflected source/owner/namespace C1 labels before path/SQLite access; Memory v1 untouched |
| Planner DAG admission | `6c466bc38fe46e714011b6d711573d8a9073c276` | `d1183465ee5753f3f3edfc4b8f5c7e5cfa836d57` | 33 | Standalone PlanGraph refuses C1 in step/dependency/tool/capability/scope before request hash and graph allocation; PlanStep/ToolCall v1 unchanged |

**Total: 4 non-UI source fixes, 99 newly authored parametrized cases**, plus positive compatibility fixtures. The tests exercise Unicode C1 denial, retained multilingual behavior, frozen public v1 boundaries, and mock/no-dispatch. These counts are **authored** cases, not a PASS claim. All changes were saved using normal GitHub Contents API operations on Draft PR #8. No raw Git object, alternate write path, forced ref update, main merge or UI change.

## CI / evidence discipline

- Prior Run970 exact checkpoint `8eeedfbc571231db4e6805760cf482e0e1401be0`: [CI #44328854791](https://github.com/Iam-2squared/ark-ai/actions/runs/44328854791) **GREEN / SUCCESS, six Windows/Ubuntu × Python 3.11–3.13 jobs** verified at invocation start.
- Run971 package-triggered CI runs [#44339558634](https://github.com/Iam-2squared/ark-ai/actions/runs/44339558634), [#44339673606](https://github.com/Iam-2squared/ark-ai/actions/runs/44339673606), [#44339746182](https://github.com/Iam-2squared/ark-ai/actions/runs/44339746182), [#44339819302](https://github.com/Iam-2squared/ark-ai/actions/runs/44339819302), [#44339959293](https://github.com/Iam-2squared/ark-ai/actions/runs/44339959293), [#44340025318](https://github.com/Iam-2squared/ark-ai/actions/runs/44340025318), [#44340161160](https://github.com/Iam-2squared/ark-ai/actions/runs/44340161160) were **IN PROGRESS or QUEUED** at first sampling. The latest Planner test commit `d1183465...` and later documentation/checkpoint commits may have separate runs. Exact-head all-six GREEN is **not** inferred from earlier success.
- No local end-to-end pytest/Ruff or real physical-PC evidence was executed. Source/test files were re-read from exact committed HEAD for UTF-8 content and 100-character source line-budget checks; CI remains authoritative.

## Preservation and blockers

V1/V2/Local UI/Launcher frozen evidence, Memory v1, Observation Envelope v1, PlanStep/ToolCall v1, V3/contamination/provenance/reproducibility and protected evaluation boundaries unchanged. Draft PR #5 remains protected/unmerged; Draft PR #9 paused/unmerged/untouched; Draft PR #8 stays unmerged. No paid or potentially billable service or external GPU, candidate generation/promotion, secrets/new connections, real capture, mock-to-live dispatch, destructive action, unknown WRITE automatic replay or unauthorized merge. In-process input/digest checks are **not** provenance authentication, authorization, trusted clock or external exactly-once evidence.

## Follow-up

1. Resolve exact latest source+test CI six-platform results; investigate any FAIL and patch only affected semantics without bypassing normal GitHub writes.
2. Continue Memory WAL/SHM and CAS/ABA/expiry coherent snapshot recovery under the frozen contract.
3. Continue Planner crash/terminal recovery and verified ToolRegistry/PermissionGate → durable authorization → audit-before-action disconnected integration.
4. Continue privacy-safe Personal Context, occurrence/replay-safe Proactive Scheduler, observation fixture adapters and free-only V3 guards. Keep UI paused.
