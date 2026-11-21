# Run784 — Non-UI exact CAS, Memory pre-access triage, Planner double sweep

**Report captured:** 2026-11-11T13:47:55.354+09:00 JST, from the connected runtime's administrative clock. This is **not** ARK trusted time or human approval.

**Scope:** public repository `Iam-2squared/ark-ai`, draft/unmerged PR #8, branch `research/jarvis-foundations`. Initial work-basis HEAD `42e2b63a82e1413265e31d62fe7f1875ee63a630`. Last implementation/test HEAD `65f61705f4123f68a5915b87c29ea4f4b0037d89`. PR #5 protected V3 and paused UI PR #9 remain Draft/unmerged and untouched; all V1/V2/Local UI/Launcher freezes unchanged.

## Package A — local pre-action audit exact-scalar CAS

- Source: `src/ark/agency/disconnected_atomic_preaction_ledger.py` at `f72d8fceaba01954df96f797c6735493ea8d09cf`; synthetic regression cases at `e1e7c3533f19b4d34786069eb109fc01a97af20b`.
- `inspect` and `reserve` compare exact `(count, tip_sha256)` images rather than the replaceable dataclass `__eq__`. A caller-retained witness is pinned before SQLite and rechecked immediately before COMMIT; drift rolls back the two-row intent+audit transaction.
- Three regression cases cover forged `__eq__`, stale read and write CAS, and mutation during SQLite scan; persisted audit remains single-store only. The source-only/new-test CI snapshots initially all failed Ruff `E501` on the 102-character refusal line. A semantics-neutral line wrap was saved at `4eeafc3f28d5c7028086d9a066356add59497980`; matching CI was still in flight at report capture.

## Package B — opt-in Memory post-COMMIT triage preflight

- Source `src/ark/memory/postcommit_uncertainty_review.py` at `8de208effc51fbbd03e0a58e389deb0ddb004375`; thirteen cases at `27a8df31b28cf8fe8944a347522bf41fb06eb1b3`; correction of actual Python lone-surrogate fixtures at `17f91d78e502f5c428d9d0b744ca5ffe09629411`.
- Before private SQLite read, reject a reflectively mutated proposal with invalid UTF-8 source/scope/content, oversized or non-string metadata, or noncanonical SQLite expiry. Valid unchanged observation remains strictly manual-only; frozen public Memory v1 CRUD and schema unchanged.
- No proof of which caller committed; no read result authorizes a retry or real action. Investigate global cross-scope event high-water coverage separately after exact-head GREEN rather than changing the in-flight path.

## Package C — Planner local double-read recovery fence

- Source `src/ark/agency/disconnected_planner_epoch_recheck.py` at `a087c89d4e2fba1f64ad864c02b9d16407e43264`; two regression cases at `65f61705f4123f68a5915b87c29ea4f4b0037d89`.
- An independently retained Planner prefix is replay-checked in two read-only sweeps. A synthetic FAILED transition committed while the original RUNNING recovery is classified now produces a refusal instead of an apparent `MATCH_AT_READ`. Stable records still give non-authorizing local observations.
- The second scan does **not** create a lock, cross-DB atomicity, trusted clock, external effect evidence or freshness after return. Ambiguous RUNNING/WRITE remains manual, without replay.

## Evidence, CI limitations, and next priorities

- Baseline [#42955538526](https://github.com/Iam-2squared/ark-ai/actions/runs/42955538526) at exact initial HEAD `42e2b63...`: **Windows and Ubuntu × Python 3.11/3.12/3.13 = 6/6 GREEN**.
- Audit intermediate [#42960706019](https://github.com/Iam-2squared/ark-ai/actions/runs/42960706019), [#42960751632](https://github.com/Iam-2squared/ark-ai/actions/runs/42960751632), and subsequent Memory intermediates through [#42960920062](https://github.com/Iam-2squared/ark-ai/actions/runs/42960920062) were **6/6 FAIL** from the one observed Ruff E501 audit line; repaired at `4eeafc3f...`. New tests (3+13+2=18) must not be treated as fully passing until matching code/test CI is GREEN.
- At report capture, audit fix [#42961073573](https://github.com/Iam-2squared/ark-ai/actions/runs/42961073573) was IN PROGRESS and Planner [#42961202474](https://github.com/Iam-2squared/ark-ai/actions/runs/42961202474), [#42961260640](https://github.com/Iam-2squared/ark-ai/actions/runs/42961260640) were not proven all GREEN. Later CI results must be recorded accurately in canonical status; no manual duplicate workflows.
- **Next:** (1) inspect failing jobs from the exact latest test HEAD and repair narrowly, (2) Memory global event integrity/COMMIT-UNKNOWN reconciliation, (3) Planner durable crash state, (4) isolated registry+PermissionGate+trusted audit-before-action+disconnected mock tests, (5) Personal Context privacy and V3 free-only guards.
- **Hard boundaries:** no UI/frontend work, real ToolBackend, real notifications, paid/external GPU or services, Candidate generation/promotion, protected V2 evaluation, new credentials, physical PC claims, destructive operations, force push, frozen evidence changes or main merge. No independent custody or authenticated consent established. Full ARK/JARVIS remains **NOT_PASSED**.
