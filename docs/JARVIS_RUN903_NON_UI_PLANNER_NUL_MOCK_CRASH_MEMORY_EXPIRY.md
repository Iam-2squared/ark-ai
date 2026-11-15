# ARK AI Run903 — Planner NUL ingress, disconnected mock crash matrix and Memory expiry/CAS restart

**Scope:** Non-UI, reversible local-first foundations in Draft PR #8. **Overall ARK/JARVIS: NOT_PASSED.** This report describes source and authored tests, **not** certified success of current CI until the exact HEAD's six jobs finish.

## Work basis and concrete changes

- **Initial inspected HEAD:** `f8f1505e559b2843e4dc5b1ab207dd9d954abc83`, Draft PR #8. [CI 43749883848](https://github.com/Iam-2squared/ark-ai/actions/runs/43749883848) completed GREEN across Windows/Ubuntu × Python 3.11–3.13; those checks predate this work.
- **Planner NUL fail-closed ingress:** [source commit `5c4359ea`](https://github.com/Iam-2squared/ark-ai/commit/5c4359ea3fdeb255a65e785b0f1642bc43bcb0c7) adds a bounded NUL separator rejection to `_admit_graph_label` before plan maps, SQLite journal and ToolCall request hashing. Frozen `PlanStep`/`ToolCall` contracts are untouched. [7-case regression `7091a28b`](https://github.com/Iam-2squared/ark-ai/commit/7091a28b7f26d1915671415a2ddc7de80d013de5) covers five post-init reflected label fields, originally accepted constructor label, and valid Unicode readiness.
- **Offline registered WRITE crash boundary integration:** [5-case regression `009dc88e`](https://github.com/Iam-2squared/ark-ai/commit/009dc88e3c55f65d3d8acb8d2396632d13a3b2d0) exercises independent Plan Journal, Occurrence and Audit stores. Four injected stop stages require a cold restart to preserve `RUNNING/UNKNOWN`, prohibit replay even with a fresh process-local PermissionGate, and retain only actually committed synthetic rows. A fifth case lets an independent sibling mock step finish without unquarantining an UNKNOWN root. Registered `execute` is an intentional exception-raising sentinel and must receive zero calls.
- **Memory expiry/CAS multi-handle:** [2-case regression `19ebb419`](https://github.com/Iam-2squared/ark-ai/commit/19ebb419fb14d1876355e4cea8281d341070f8db) checks that an old CAS cannot recreate a row purged by another handle, that unrelated namespace data persists, and that bounded expiry over restarts yields one event per deleted row without duplicate expiration. Synthetic clock and fixture contents only; no external data or physical machine action.

**Total:** three coherent non-UI packages, one production ingress hardening, and **14 authored tests** (7 + 5 + 2). No claim that new tests or latest HEAD are GREEN until verified by GitHub CI. Package write basis was re-read from PR #8 before each normal Contents API operation. No force-push or raw Git object update.

## Invariants and boundaries

- No real ToolBackend invocation, live camera/microphone, network tools, notification, actual user consent, real WRITE, or training; synthetic local receipts are not independent authority.
- Existing V1/V2, Local UI, Launcher, protected final evaluations and PR #5 frozen contracts remain untouched. PR #9 UI remains paused Draft/unmerged. PR #5, #8 and #9 must stay Draft/unmerged; no main merge.
- SQLite WAL/SHM/rollback-journal last-close and two-process Privacy Revocation contender race remains **unresolved**. A valid durable veto with a rejected loser is a genuine UNKNOWN response, not a reason to suppress the failure, relax a test or retry consent. Windows/Ubuntu failures from other runs are not evidence that this lane has passed.
- Zero-cost only: no external GPU, paid API, credentials, new account connection, protected Candidate generation/promotion, physical PC steps or destructive operations.

## Validation plan and priorities

1. Collect current-head and intermediate six-environment CI statuses. If failures appear, distinguish regression, test expectation error and independently observed WAL sidecar race; apply the smallest semantics-preserving correction through standard GitHub file writes.
2. Keep the WAL/SHM race blocked without weakening the security predicate; investigate safe serialization/open-handle custody separately.
3. Advance Memory event/CAS/expiry independent witness, Planner COMMIT-UNKNOWN reconciliation, immutable Registry/PermissionGate, trusted audit-before-action and disconnected Mock Execution only after their required exact-head GREEN.
4. Continue privacy-safe Personal Context, Proactive scheduler and Observation back-end fixtures, detached free-only V3 guards. No frontend work.

**Technical report write-basis HEAD:** `19ebb419fb14d1876355e4cea8281d341070f8db`. The GitHub commit resulting from writing this report must be obtained from the standard API response.
