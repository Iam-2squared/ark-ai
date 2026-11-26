# ARK AI — Run726 non-UI privacy CI repair and offline protocol fences

**Scope and work basis:** Draft PR #8 `research/jarvis-foundations`, initial exact head `8752922a5e42e9c2ecd88882f500f308ad7b3910` (Run725 checkpoint). All writes used ordinary, sequential GitHub Contents API calls after re-reading the PR HEAD. No UI, frozen contracts, model evaluation, paid services, physical PC, live dispatch, irreversible operation or main merge.

## A. Real CI log: privacy retained witness preaccess denial

- [Run725 checkpoint CI #42542966045](https://github.com/Iam-2squared/ark-ai/actions/runs/42542966045) finished **FAIL 6/6**. Inspected Ubuntu 3.11 and Windows 3.12 actual job logs. Each reported two older assertions in `tests/test_privacy_revocation_phase_epoch_run393.py` expecting a hostile `_validate` callback to execute. The new, stronger import-original schema-validator check correctly rejected **before** callback execution. Ubuntu 3.11: **11,358 passed / 2 failed / 1 skipped**; Windows 3.12: **11,297 passed / 2 failed / 62 skipped**.
- [Test-only correction `3472936`](https://github.com/Iam-2squared/ark-ai/commit/3472936ad648809836c41f0d353e742ff489e18a) now requires `changed is False`, retaining typed rejection and zero hostile callback execution. No private SQLite row is disclosed or changed; no production privacy code was weakened.

## B. Planner — pinned detached expected READ manifest protocol

- [Source `3ce9ba2`](https://github.com/Iam-2squared/ark-ai/commit/3ce9ba29be1524a16b68ca65675e10da7b192bce) pins the import-original manifest schema, digest domain, byte/step budgets, and request/step/SHA regex identities in the existing `_authority` gate. An in-process mutation is now rejected before using a widened parser, altered receipt namespace or unreviewed data budget.
- [15 parameterized local tests `7212c77`](https://github.com/Iam-2squared/ark-ai/commit/7212c77463d0fb9639aaf7fee08e2e2b1f015c8d) cover 7 protocol substitutions in both file write and read paths, plus a reentrant post-write domain drift. A created file under an unknown publication outcome remains quarantined, not implicitly removed/retried. Unmodified read/write remains covered by existing manifest tests.
- Manifest and its local SHA-256 remain caller-controlled, **not independent provenance**, real external READ evidence or replay authority. No journal contract or frozen gate was changed.

## C. Memory — manual COMMIT-UNKNOWN triage protocol

- [Source `2f70893`](https://github.com/Iam-2squared/ark-ai/commit/2f70893be155bb42f7a45a3d1176f3ae69f9f4b7) pins the manual report digest domain, event digest domain and bounded event scan budget, using the existing repeated report carrier check before private SQLite and after synthetic callbacks.
- [7 synthetic tests `11c8b9a`](https://github.com/Iam-2squared/ark-ai/commit/11c8b9ac29d5b998d3b068b79f1b1c141e44a754) exercise each preinstalled and reentrant substitution, plus unchanged deny-only triage. They require zero uncontrolled private SQLite opens before the early check and no mutation/replay. `MemoryCommitTriage` cannot prove commit authorship, user consent, trusted time, or automatic retry.
- [Intermediate CI #42547776516](https://github.com/Iam-2squared/ark-ai/actions/runs/42547776516) completed **FAIL 6/6**: Ubuntu 3.11 actual log identifies a Ruff I001 import-order error in the new test, **before pytest**. The import layout was corrected without altering security assertions in [`cccf66d`](https://github.com/Iam-2squared/ark-ai/commit/cccf66d07316261fd33858979b066d1a458ebf60). The new occurrence test imports were proactively ordered in [`23350ec`](https://github.com/Iam-2squared/ark-ai/commit/23350ec552de943a396b79ca98b681f493451654).

## D. Disconnected authorization — synthetic durable occurrence format

- [Source `ebf4a2b`](https://github.com/Iam-2squared/ark-ai/commit/ebf4a2b50d19d8b7cacea60f3140eba7b173ccbc) pins local SQLite schema DDL, maximum timestamp and five occurrence/token/registry/bound/request ID regex identities; the established configurable fixture capacity remains subject to existing zero/full/concurrent capacity tests. The protocol fence is consulted at store creation, row validation, read-only count and reservation ingress. [Source `c6a41c2`](https://github.com/Iam-2squared/ark-ai/commit/c6a41c242ba0258cf11b2feaf36c5276784a2500) rechecks it after registry callbacks and before/after SQLite COMMIT.
- [23 synthetic regressions `c88d64a`](https://github.com/Iam-2squared/ark-ai/commit/c88d64afef6a01c013f22f335305647f15e92d56) cover 7 pinned-protocol substitutions × initialize/count/reserve, one reentrant registry bind, and one post-COMMIT protocol drift. A committed local one-shot reservation is never claimed rolled back by an error. The same token remains reserved on restart; there is no external dispatch or automatic replay.
- The capacity limit is deliberately test-configurable, with fail-closed row counting and pre-INSERT enforcement retained. It is not an authenticated quota or general-purpose permission mechanism.
- This is a **disconnected mock fixture**, not authenticated human consent, issuer identity, a trusted clock, or exactly-once real-world execution. No actual tool backend, approval or external action runs.

## Validation and gates

- **New parameter-expanded tests authored: 45** = Planner 15 + Memory 7 + occurrence 23. **Three** non-UI production modules and **three** new test files; plus one inherited privacy test correction and two new-test import-order fixes.
- Latest source/test branch HEAD before this report: `23350ec552de943a396b79ca98b681f493451654`; its automatic [CI #42548202602](https://github.com/Iam-2squared/ark-ai/actions/runs/42548202602) subsequently showed real Ubuntu 3.11 failures (**11,402 PASS / 6 FAIL / 1 SKIP**) at the earlier source HEAD: three new Memory test hooks were deliberately still installed during the follow-up get, and three existing synthetic occurrence capacity tests used their established mutable test budget. [Memory fixture scoping fix `9a87ff5`](https://github.com/Iam-2squared/ark-ai/commit/9a87ff5290fc2d17db4ff76b304f0d0259fc2f6a) limits the hostile SQLite hook to the preaccess assertion. [Occurrence source `65a2f80`](https://github.com/Iam-2squared/ark-ai/commit/65a2f8000fde5c37f7c474353099179db66eb257) preserves zero/full/concurrent bounded-capacity injection without changing the actual insertion limit checks, while [tests `8b3499c`](https://github.com/Iam-2squared/ark-ai/commit/8b3499ca22e00b8e952c38daff20374b626acd8a) and [`51b4511`](https://github.com/Iam-2squared/ark-ai/commit/51b45114178963614f4b12861bdaa5496cd35a75) target only pinned protocol fields. The newer source/test HEAD CI is NOT yet 6/6 GREEN. No 6/6 GREEN or 48-case final PASS claim. Exact checkpoint-result HEAD CI will be a *different* automatic run after the final status update.
- No local full Ruff/pytest or physical Windows verification was available in this run. Earlier-head CI failures are not misreported as fixed-head PASS. All subsequent CI failures must be diagnosed from actual logs, without bypassing normal source/test write safeguards.
- Main and PR #5/#9 remain untouched and all three PRs remain Draft/unmerged. Frozen V1/V2/Local UI/Launcher evidence, V3 Contract 1, protected V2 final evaluation, free-only V3 restrictions and UI pause are unchanged. ARK/JARVIS remains **NOT_PASSED**.

## Next plan / 今後の方針

1. Confirm the **exact final source/checkpoint-result HEAD** six CI jobs. For failures inspect actual Windows/Ubuntu logs, patch the smallest safe test or semantic issue, and switch to an independent non-UI lane during automatic CI.
2. Memory: independent retained row/event witnesses, cross-scope CAS/ABA and COMMIT-UNKNOWN restart-safe manual reconciliation with no actor attribution or retry.
3. Planner: manifest publication/recovery, independent READ input custody and terminal DAG projection under detached evidence.
4. Registry → exact-type PermissionGate → durable one-shot occurrence → trusted-clock audit-before-action → **disconnected/mock** executor; only integrate after corresponding lower-level exact-head GREEN evidence.
5. Privacy-safe Personal Context, proactive state, observation fixture contracts and free-only V3 approval/identity/path guard reviews. Keep PR #5 and paused PR #9 Draft/unmerged, no paid resources/real tools/protected evaluations/main merges.
