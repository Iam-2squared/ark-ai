# ARK AI Run917 — CI repair, inert ToolRegistry, Memory CAS/ABA and prehydration

Prepared 2026-11-16 JST; evidence is scoped to the exact commit IDs and GitHub Actions runs below. This is **non-UI, disconnected/free-only** work. No real backend, paid API, account, physical PC, external effect, protected evaluation, Candidate, promotion or migration was used.

## Source and dependency audit

Started from Draft PR #8 head `c03a3fef124d5ed9541680205a287e90bfb8a020`, main `7a843f17eb96ed13d66f23b58b06406b3002e405`. Protected Draft PR #5 and paused Draft PR #9 were open/unmerged. Canonical Run916 checkpoint had recorded **24 authored cases**, but its exact [CI #43836800587](https://github.com/Iam-2squared/ark-ai/actions/runs/43836800587) has now finished **FAIL 6/6**, *not* GREEN. Ubuntu Python 3.11 reported **1 failed, 16,442 passed, 1 skipped**: `test_unchanged_quarantine_catalog_is_accepted_by_local_constructor`. The synthetic positive fixture used `interval_ms=100` while the existing frozen `_policy_epoch` requires `interval_ms>=1000`. Existing rejection behavior is correct; no policy/contract relaxation was made.

## NEW packages in this invocation

1. **CI repair** — [`8ac21b8c`](https://github.com/Iam-2squared/ark-ai/commit/8ac21b8c544d2426ed1112a742fe86218d99c600). One legacy Run916 positive-control test now constructs a policy with `interval_ms=1000`; malformed SQLite synthetic negative guards remain unchanged. No production change in quarantine.

2. **ToolRegistry descriptor identity** — [`1b2582f2`](https://github.com/Iam-2squared/ark-ai/commit/1b2582f2235c2990d3aa735900e1fc78ab290ef1). Six newly authored inert tests: reject property-based `backend.execute` without evaluating it; detect class-level callable replacement in `bind`, `resolve`, and revision read; reject reflected registration effect and backend replacement. All fixture backends deliberately raise if executed. This is no backend attestation or WRITE authorization.

3. **Memory cross-handle CAS and ABA** — [`54befb5a`](https://github.com/Iam-2squared/ark-ai/commit/54befb5a4a16c9690eaf289ffbc7d62b2dfa9751). Four newly authored synthetic tests: stale update/delete from an older SQLiteMemoryStore handle must not append an event or overwrite a newer write, and delete/recreate numeric revision reuse must be reported as ABA ambiguity, without granting write, erasure or generation authentication.

4. **Memory generation reviewer prehydration** — [source `6a9f3084`](https://github.com/Iam-2squared/ark-ai/commit/6a9f3084e351ed7816c2366d4ed9fe13e0ba0705) and [five-test `f8d402af`](https://github.com/Iam-2squared/ark-ai/commit/f8d402af740b4cf2bd180f720f74c01e0fcc47d8). The separate `review_memory_revision_reuse` function had a private `SELECT *` and event `fetchall()` without SQLite-side TEXT preflight, unlike the store's normal `get` path. The new read-only checks in its **same BEGIN snapshot** require bounded owner/namespace/source/content/metadata/digest bytes and bounded event owner/namespace/operation, rejecting tampered rows before Python hydration. Five new fault/positive cases use disposable synthetic SQLite rows; no schema or external custody claims.

**New cases authored:** 6 + 4 + 5 = **15**. **15 is not an all-platform passing count.** This invocation also corrected the single Run916 positive-control fixture. Source+test write paths use normal GitHub Contents operations; no force-push, raw-Git workaround or main merge.

## Exact CI observations — do not promote earlier HEADs

- Prior [#43836800587](https://github.com/Iam-2squared/ark-ai/actions/runs/43836800587), head `c03a3fef...`: **FAIL 6/6**, root cause described above.
- [#43842588106](https://github.com/Iam-2squared/ark-ai/actions/runs/43842588106), fix `8ac21b8c...`: **IN PROGRESS**, Ubuntu 3/3 GREEN, Windows 3 pending at observation.
- [#43842934612](https://github.com/Iam-2squared/ark-ai/actions/runs/43842934612), registry `1b2582f2...`: **IN PROGRESS**, Ubuntu 3.11 and 3.12 GREEN, other jobs pending.
- [#43843177933](https://github.com/Iam-2squared/ark-ai/actions/runs/43843177933), Memory CAS `54befb5a...`: **IN PROGRESS** at observation.
- [#43843501999](https://github.com/Iam-2squared/ark-ai/actions/runs/43843501999), Memory generation source `6a9f3084...`: **IN PROGRESS** at observation.
- [#43843638622](https://github.com/Iam-2squared/ark-ai/actions/runs/43843638622), Memory generation test `f8d402af...`: **QUEUED/IN PROGRESS** at observation.

These intermediate observations cannot certify final source/test, later report or checkpoint commits. No duplicate manual CI launch.

## Frozen boundaries, risks and next plan

Frozen V1/V2/Local UI/Launcher contracts/evidence untouched. Draft #5 protected V3 approval/reproducibility/human-review/Candidate gates unchanged, Draft #9 UI paused/unmerged, PR #8 remains Draft/unmerged, and main unchanged. No paid API/compute, real model or adapter weights, trusted clock, user tokens, secrets, new external accounts, real ToolBackend dispatch, UNKNOWN replay, automatic promotion, protected evaluation, deletion or destructive action. Synthetic Memory mutations exist only in disposable local test databases.

Open gaps: all-six CI on **exact final HEAD** not yet certified; unresolved two-process SQLite WAL/SHM last-close alias/race (UNKNOWN/FAIL); no independent historical provenance/sidecar custody, trusted action clock, external exactly-once guarantee, human approval or real GGUF PC verification. Overall ARK/JARVIS **NOT_PASSED**.

Priorities: certify latest exact HEAD CI and repair genuine regression without weakening guards; strengthen separately held Memory provenance and CAS/event high-water, Planner COMMIT-UNKNOWN cold recovery; isolate disposable WAL/SHM process phases; only after GREEN integrate strict Registry/PermissionGate and audit-before-action with disconnected mock execution; continue privacy-safe Personal Context and free V3 guards without resuming UI.
