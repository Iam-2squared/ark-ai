# ARK AI Run865 — bounded disconnected SQLite ingress across proposal, READ, durable markers and due slots

**Observed at:** 2026-11-14T06:51:57.803Z UTC (reporting wall clock only; NOT trusted approval/issuer/action/audit/consent time). **ARK/JARVIS: NOT_PASSED.** Work saved only on `research/jarvis-foundations`, Draft PR #8, local-first/free-only/disconnected. **All new UI/frontend work paused.**

## Exact source basis and independent CI

Initial branch/PR work basis: `f1ea98c74b19e5993f261d40659ee6a0584434dd` (Run864 checkpoint). The previously queued checkpoint [Actions #43563646004](https://github.com/Iam-2squared/ark-ai/actions/runs/43563646004) is now **6/6 GREEN** (Ubuntu and Windows × Python 3.11–3.13) on that **prior exact HEAD** only. No new-head or physical PC/GGUF certification is inferred.

## NEW — four non-UI coherent work packages and 28 authored synthetic regression cases

1. **Disconnected proposal review store**: `004dcb78efd63abeae3425507b9aaca6ba79e190` source, `d81c720405145402b9617c2e7fd90ef1212758e8` tests, `186ea6086d812fbf406e239b48944ba10d20d787` oversized-DDL fixture correction (**6 cases**). SQL-side catalog count exactly 2 (table + generated UNIQUE index) and DDL bytes at most 4096 before loading any foreign SQL into Python. Require exactly one clean `PRAGMA quick_check` diagnostic, bounded by `fetchmany(2)`. Corrected the oversized test to add a synthetic column *before* the table UNIQUE constraint, verified with local isolated SQLite. The frozen proposal DDL, external human authority, Candidate and training gates remain unchanged.
2. **Detached READ receipt journal**: `eaec9dcbc2fffc1150870f35efed184c96e36a3e` source, `7f2703721ac00983c230ee1193024d2d72086586` tests, `7bc51e884a87de12d252d38aae84fde2ac6cdf3f` fixture correction (**8 cases**). SQL-side catalog count exactly 3 (marker + receipts + UNIQUE index), DDL max 4096 bytes. Bound SQLite integrity diagnostics to 2, marker rows to 2, receipt rows to `_MAX_ROWS+1` (129) before refusing a 129-row stream. Keep hash-chain/recovery/no-authority semantics and original DDL. Oversized-DDL synthetic column now precedes table UNIQUE constraint, validated with local isolated SQLite.
3. **Memory v1 + ActionAudit v1 append high-water**: `75e58bc7fd6ec2ef43df74758b0aea9c79673138` Memory, `5e1d6c9e03b60c52f75d50305ac1d279b3d7d339` audit, `5be0c252321cbad92be684e2fd2aa7ef50565df3` synthetic shared tests (**8 cases**). Read at most 2 `sqlite_sequence` rows for the relevant AUTOINCREMENT table, preserving the exact existing one-row/empty-history requirements; excessive duplicate high-water markers are rejected before any unbounded Python hydration. Two additional real in-memory duplicate marker tests verify fail-closed behavior; local v1 schema/DDL unchanged.
4. **Disconnected proactive due-slot reservations**: `6836630d5ad7bab60897c7e0e33b0caca66e9f3f` source, `6940f6b5f12735937b3a57b5ae4ab07e51eae2d6` tests (**6 cases**). Preflight SQL catalog count exactly 2 and DDL bytes max 4096, with bounded two-row SQLite integrity output, before hydrating foreign SQL. Local mock schedule fixture does not gain notification, clock, consent or execution authority.

**Total 28 regression cases authored, not an exact-latest-HEAD 6/6 PASS claim.** Source and tests were written through normal GitHub Contents API with branch-head rereads, not raw Git mutations. One local Python sqlite3 probe confirmed expected table/index counts and corrected >4096-byte synthetic DDL with an identifier before table constraints. This probe is **not** full pytest, Ruff, Windows or actual model evaluation. An isolated SQL count probe verified due-slot large-column DDL with two catalog objects.

## CI overlap / evidence boundaries

Automatic CI was triggered by normal Contents commits; there were **no manually duplicated workflow launches**. Most recent new source+test HEAD before this report: `6940f6b5f12735937b3a57b5ae4ab07e51eae2d6`; [Actions #43568311407](https://github.com/Iam-2squared/ark-ai/actions/runs/43568311407) **QUEUED** at the last verified snapshot. Other intermediate runs were queued/in progress, not GREEN-certified: proposal `d81c7204` [#43567783932](https://github.com/Iam-2squared/ark-ai/actions/runs/43567783932), READ `7f270372` [#43567912586](https://github.com/Iam-2squared/ark-ai/actions/runs/43567912586), shared high-water `5be0c252` [#43568043613](https://github.com/Iam-2squared/ark-ai/actions/runs/43568043613). Later result changes require exact-run verification, not retroactive PASS. This report and the final PROJECT_STATUS checkpoint may trigger their own CI.

## Audit, frozen contracts, remaining blockers

V1/V2/Local UI/Launcher frozen contracts and evidence unchanged; PR #5 and #9 remain untouched Draft/unmerged, PR #8 Draft/unmerged. No UI/Frontend code/tests, paid service, external GPU, real Candidate/adapter/weights, model promotion, protected final evaluation opening, credential/account provisioning, physical Windows action, main merge or real ToolBackend dispatch.

**Still NOT_PASSED:** WAL/SHM last-close/path-to-open races, independent COMMIT-UNKNOWN attribution, cross-store atomicity, trusted clock/issuer/consent, durable single-use authorization, audit-before-action external coupling, exactly-once external effects. These bounded hydration and schema checks are local corruption/availability gates only, not independent provenance or permission.

## Next plan / 今後の方針

1. Verify the newest exact source+test, report and checkpoint HEAD CI for Windows/Ubuntu × Python 3.11–3.13; on FAIL, repair minimally without changing fail-closed constraints.
2. Add stronger disposable WAL/SHM and COMMIT-UNKNOWN ambiguity probes in independent lanes. Never auto-retry unknown external effects.
3. Improve Planner crash-recovered UNKNOWN isolation, Memory coherent snapshot/CAS and expiry lineage; retain original DDL and frozen evidence.
4. Continue independent Personal Context privacy/retention/revocation, observation backend and proactive schedule fixtures, without any user data export.
5. Integrate immutable ToolRegistry, exact PermissionGate and disconnected audit-before-action/mock execution only after exact-head lower-level GREEN; keep all real actions denied.
