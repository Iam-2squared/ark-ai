# ARK AI — Run929 non-UI core: proactive CI repair, Memory event cross-scope, startup NUL requirement

Observed reporting time (Asia/Tokyo/JST): `2026-11-17T07:58:01.469+09:00`. This is a reporting clock, **not** a trusted action or approval clock.

**Branch / PR:** `research/jarvis-foundations` / Draft PR #8, open/unmerged. Work-basis HEAD `a3d2a1d148421d5ca6ff803b9714118b889b66e7` (Run928 checkpoint). New source/test HEAD before this report: `7262ac6d85e4e759f8c6b5fc3a8cf3aa49a534d5`.

## New work — three non-UI work packages, eleven authored synthetic test cases

### 1. Repair real six-matrix proactive CI failure (production fail-closed guard)

[Commit e2233851](https://github.com/Iam-2squared/ark-ai/commit/e22338513df7185b586dc2661bae6f5171c13141) inserts the existing import-original `_require_original_policy_contract()` check at entry to `review_prepared_trigger_freshness`, **before** any reflected policy identity/field read. Run928's [CI #43965083798](https://github.com/Iam-2squared/ark-ai/actions/runs/43965083798) completed **FAIL 6/6**: both Linux and Windows Python 3.11 logs show the identical single test failure `test_identity_replacement_blocks_continuity_callback_before_evidence_read` because one replaced policy `identity()` hook executed when the test correctly expected zero. The previous check inside the original `SyntheticTriggerPolicy.identity()` cannot protect a *replaced* method. This early guard preserves the expected `policy contract changed` rejection and stops injected callback execution. No relaxed checks or live behavior.

**Limit:** later reentrant mutations after the entry-time guard warrant a further review. Early deny-only checks and synthetic tests do **not** establish end-to-end trusted operation approval.

### 2. Memory owner/namespace CAS and global append integrity

[Commit 1d0b2a7](https://github.com/Iam-2squared/ark-ai/commit/1d0b2a7f40cac81425a05ae7400da11da874dbc9) adds **4 parameterized synthetic tests**. They exercise two independent SQLiteMemoryStore instances interleaving creates, updates and a delete across (a) different owners and (b) different namespaces with a shared source ID; reject stale CAS update/delete; check post-reopen scoped visibility, revision, and event pagination by global event ID. Separately, deletion of a foreign-scope event in a disposable fixture must cause the surviving scope's event reader to reject the **global append high-water mismatch**, not silently skip the gap. This is intentional corruption of a private temporary *test* store only; no user data changed.

### 3. Startup readiness lease NUL identity admission

[Source f00fad51](https://github.com/Iam-2squared/ark-ai/commit/f00fad513e9992473538f0c8f9af217979105933) rejects NUL-containing component/schema requirement strings after exact-string and UTF-8 validation, **before** using the requirement to match a readiness snapshot. [Tests 7262ac6d](https://github.com/Iam-2squared/ark-ai/commit/7262ac6d85e4e759f8c6b5fc3a8cf3aa49a534d5) add **7 cases** covering both fields × NUL beginning/middle/end and a healthy unchanged requirement. No modification of the underlying frozen StartupComponent/Launcher contracts, no actual PC startup.

## CI evidence at report-write snapshot

- Previous failing Run928 checkpoint: [#43965083798](https://github.com/Iam-2squared/ark-ai/actions/runs/43965083798), SHA `a3d2a1d1`, **FAIL six out of six**; Ubuntu 3.11: 1 failed / 16,756 passed / 1 skipped; Windows 3.11: 1 failed / 16,634 passed / 123 skipped.
- First corrected proactive source: [#43973909280](https://github.com/Iam-2squared/ark-ai/actions/runs/43973909280), SHA `e2233851`.
- Memory tests: [#43974179880](https://github.com/Iam-2squared/ark-ai/actions/runs/43974179880), SHA `1d0b2a7f`.
- Startup source: [#43974515156](https://github.com/Iam-2squared/ark-ai/actions/runs/43974515156), SHA `f00fad51`.
- Exact CI snapshot: `[{"id":43974565154,"sha":"7262ac6d","status":"queued","conclusion":null},{"id":43974515156,"sha":"f00fad51","status":"in_progress","conclusion":null},{"id":43974179880,"sha":"1d0b2a7f","status":"in_progress","conclusion":null},{"id":43973909280,"sha":"e2233851","status":"in_progress","conclusion":null},{"id":43965083798,"sha":"a3d2a1d1","status":"completed","conclusion":"failure"},{"id":43964699038,"sha":"7c0204c5","status":"completed","conclusion":"failure"},{"id":43964014776,"sha":"febf802c","status":"completed","conclusion":"failure"}]`.
- Tests are **AUTHORED**, not yet certified all-matrix GREEN at newest HEAD; no local full pytest, offline model run, external GPU or user-PC evidence was executed. Standard CI triggered by normal GitHub Contents commits; no duplicate equivalent workflow launched.

## Frozen controls and unresolved gates

Draft PR #5 remains under V3 protected approval; Draft PR #9 UI paused, no frontend writes; main untouched. Frozen V1/V2/Local UI/Launcher, protected evaluation, Observation v1 and V3 provenance/reproducibility boundaries unchanged. No training, Candidate generation/promotion, model weights, protected final evaluation, paid/external services, new credentials, real ToolBackend actions, actual PC work, irreversible changes, automatic ambiguous replay, or main merge.

**ARK / JARVIS NOT_PASSED.** The canonical PROJECT_STATUS checkpoint after this report must be confirmed by its actual returned commit and blob; report-source HEAD is not a completion claim.

## Next plan / 今後の方針

1. Confirm the newest six-job CI by **exact commit SHA**; inspect remaining failures and fix without weakening any security semantics. Only integrate dependents after GREEN.
2. Review the reentrant post-entry freshness hooks after first source CI, separately from the in-flight validation path.
3. Continue disposable WAL/SHM process alias and Memory coherent CAS/expiry/event snapshots, Planner crash/COMMIT-UNKNOWN manual-only evidence.
4. Keep registry-bound ToolRegistry, exact PermissionGate, durable occurrence/one-shot approval, trusted-clock audit-before-action and disconnected mock **isolated and non-dispatchable** pending original provenance and atomicity gates.
5. Continue Personal Context privacy, proactive, Observation backend and free V3 guard lanes; zero spend, no UI.
