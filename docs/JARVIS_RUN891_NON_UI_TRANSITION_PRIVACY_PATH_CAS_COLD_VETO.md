# ARK AI Run891 — bounded Planner transition IDs, privacy SQLite path admission and cold durability joins

**Observed at (Asia/Tokyo): 2026-11-15T16:54:47.619+09:00.** This is an untrusted runtime wall clock, not permission or provenance.

**Status:** non-UI, disconnected, Draft PR #8, JARVIS overall **NOT_PASSED**. Initial exact work-basis HEAD: `1df7af250a78b4d95886a477eb8f77425c7dbb8c`. Starting work-basis CI [#43687825354](https://github.com/Iam-2squared/ark-ai/actions/runs/43687825354) is **GREEN 6/6** Windows/Ubuntu × Python 3.11–3.13, verified by individual completed successful job records before Run891 writes. That GREEN does **not** certify later commits.

## Four independent non-UI work packages — 14 authored regression cases

1. **Planner transition ingress:** source `ae6c84bee5d3716c70808d8200e1ebaeed0c8e48`, tests `31a914bba9bd77325b5e6fb9f02a107018d2a9fc`. The existing `_admit_graph_label` validates a `transition(step_id=...)` caller value before dictionary state lookup: up to 4096 encoded UTF-8 bytes, no invalid lone surrogate. Existing exact-string and blank-ID classifications remain intact. New 5 parametrized/standalone tests deny ASCII/UTF-8 overlength, invalid Unicode and hash-bearing str subclasses while admitting a 4096-byte legal ID. This is input admission only, **not** protected dispatch or nested-JSON attestation.
2. **Memory concurrent-handle CAS/audit:** test `c143f781f68a3056400cbe4dbc7e681c0e4681d3`. Three synthetic SQLite cases check that a stale CAS attempt across separate store objects does not replace the winner or consume an append event ID; owner/namespace CAS remains independent; expiry emits a terminal event without resetting unrelated live data. The frozen Memory v1 DDL and implementation are untouched.
3. **Privacy SQLite pathname preflight:** source `564be8632083ead8baa57108b4fc9b034c2e594c`, tests `47e02161f6c7d246ad27da8f3bebd3019a5b7730`. Before any `lstat`, `resolve` or SQLite connection, reject NUL, overlong character paths and encoded absolute paths whose worst-case SQLite `-journal` suffix would exceed 4096 bytes; malformed encoding is also denied. Four synthetic cases cover the three path classes plus normal veto/restart behavior. This **does not** solve the independent-process disappearing-inode sidecar race or prove atomic file ownership.
4. **Cold Planner UNKNOWN × privacy veto join:** tests `6cb908b2ebed99f86eef7fff00f66d32e54e800c`. Two disposable-store cases couple a recovered RUNNING journal (ambiguous; no auto-replay/dispatch) with a local privacy revocation (private context rejected). Unrelated synthetic notes may be reviewed only as a non-authoritative in-memory preview. No real tools, consent, model inference, notification or cross-store atomic transaction.

**Source/test result HEAD before this report:** `6cb908b2ebed99f86eef7fff00f66d32e54e800c`. Normal GitHub Contents API only; PR #8 remains Draft/unmerged. Tests are **authored, not certified** until CI on that exact HEAD completes. A container clone was unavailable because `github.com` DNS resolution failed; there was no local full pytest or Ruff run.

## CI evidence at the latest sampled state

- [Planner source CI #43691604264](https://github.com/Iam-2squared/ark-ai/actions/runs/43691604264): **IN PROGRESS** at last inspection.
- [Planner tests CI #43691629683](https://github.com/Iam-2squared/ark-ai/actions/runs/43691629683): **IN PROGRESS**.
- [Memory tests CI #43691715111](https://github.com/Iam-2squared/ark-ai/actions/runs/43691715111): **IN PROGRESS**.
- [Privacy source CI #43691785625](https://github.com/Iam-2squared/ark-ai/actions/runs/43691785625): **QUEUED**.
- [Privacy regression CI #43691842705](https://github.com/Iam-2squared/ark-ai/actions/runs/43691842705): **QUEUED**.
- [Full cross-system fixture CI #43691968662](https://github.com/Iam-2squared/ark-ai/actions/runs/43691968662): **QUEUED**.
- The report and final checkpoint commits will trigger their own automatic PR CI; their IDs and conclusions are unknowable before the commits. **No Run891 exact-head 6/6 GREEN is yet claimed.** No manual duplicate workflow dispatch was requested.

## Unchanged gates and next plan / 今後の方針

Frozen V1/V2/Local UI/Launcher evidence and contracts remain unchanged. Draft #5 stays protected/unmerged, paused UI Draft #9 stays untouched/unmerged, and JARVIS Draft #8 stays unmerged. No UI/frontend changes, external GPU, paid API/service, physical-PC action, Candidate/weight generation, protected V2 final evaluation, human approval, privacy consent, real backend execution, destructive mutation or main merge.

**Open blockers:** Windows SQLite WAL/SHM last-close disappearance and revocation competing-process sidecar refusals; uncertain post-COMMIT response across multiple stores; independent trusted time/custody/user consent; physical GGUF verification. A failed response can follow a durable commit: **do not automatically retry**.

**Priority after this HEAD:** (1) verify actual six-job CI and repair any failures without weakening guards; (2) isolate ordinary SQLite last-close failures with safe bounded diagnostics; (3) keep Memory CAS, Planner UNKNOWN and audit-before-action exact-head GREEN; (4) continue isolated Registry/PermissionGate/Mock integration, no action authority; (5) maintain free-only V3 and privacy-sensitive context/observation contracts. All development remains non-UI until explicit resumption.
