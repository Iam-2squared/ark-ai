# ARK AI Run631 — Non-UI CI recovery and local-only receipt pre-execution custody

**State:** Draft PR #8 only. Not merged, not JARVIS PASS, no tool dispatch, no external
compute or training. This report records code/test changes and actual CI observations,
not an authenticated audit time, human approval or physical-machine result.

## Exact work basis and saved work

- Starting branch HEAD (Run630): `7f64df5b419c1f0c5097196109b7e9aef8979e04`.
- Branch: `research/jarvis-foundations`, Draft PR #8.
- **CI repair** commit `c3b1eabfc4255aa8af0e8211423be106a6354397`:
  `tests/test_clock_numeric_carrier_custody_run433.py` now expects the original
  synthetic-clock initializer guard to reject a counterfeit initializer BEFORE it
  executes (and asserts zero calls). Earlier exact-head CI
  [#42007047939](https://github.com/Iam-2squared/ark-ai/actions/runs/42007047939)
  was 6/6 **FAIL**: two parameterized tests expected a later 'constructed clock
  chain link' error but received the correct earlier 'synthetic clock denial
  descriptor changed'. The corrected clock-test HEAD
  [#42013276247](https://github.com/Iam-2squared/ark-ai/actions/runs/42013276247)
  was **6/6 GREEN**, Ubuntu and Windows Python 3.11–3.13.
- **Memory COMMIT-UNKNOWN dual review**, source
  `92c7b6e94ef4d307639c84ca6015d3b249a40b5e`, tests
  `ba3bacb9c8b1856de250392f61d11e80de7c318c`:
  `ambiguous_commit_pair_review.py` now pins import-original slotted field
  descriptors and constructor/attribute lookup hooks for the result and both
  child receipts. Review before database reads, around independent child
  callbacks and before final result construction remains fail-closed.
  **14 parameter-expanded new cases authored** in
  `test_memory_ambiguity_pair_carrier_original_run631.py`, including forbidden
  descriptors and late child callback mutation. No writer attribution, consent,
  true cross-process atomicity or automatic retry.
- **Planner restart-only receipt**, source
  `c3cffd367ef44971637f9c20c122c6fc924ebbad`, tests
  `ab647051c10c8c4e2dfde2bf0d4642b4d7a9d52e`:
  `planner_journal_review.py` pins original recovery receipt slots, constructors
  and lookup hooks, protecting read-only recovery and local journal admission.
  **10 new parameter-expanded cases authored** in
  `test_planner_journal_receipt_field_original_run631.py`. Recovered RUNNING
  remains ambiguous; no dispatch or automatic replay.
- **Offline Personal Context redaction fixture**, source
  `57ff9f1fa8db23e477ded6c379c9417f521d9081`, tests
  `c69558ce61b541ed1498f59449e80069d485494e`:
  `offline_context_redaction.py` pins original span and result class identities,
  slotted fields, constructors and lookup hooks before synthetic source hashing,
  and across reentrant hash/serialization callbacks. **15 new cases authored**
  in `test_offline_redaction_span_receipt_custody_run631.py`. A complete mask
  still is not real erasure, authenticated consent or export authorization.
- **Accounting:** 4 coherent packages, 39 new parameter-expanded pytest cases
  **AUTHORED, NOT claimed local PASS**, one prior clock test's 2 cases corrected,
  seven source/test file paths changed across seven ordinary GitHub Contents
  commits through `c69558ce61b541ed1498f59449e80069d485494e`.
  No local clone/pytest/Ruff: container could not resolve `github.com`.
  Automated GitHub CI is the only executable test evidence; CI for later
  exact heads must not inherit the earlier clock-fix GREEN.

## CI at report preparation (2026-11-05 JST)

- [#42013276247](https://github.com/Iam-2squared/ark-ai/actions/runs/42013276247),
  exact clock-fix HEAD `c3b1eab...`: 6/6 **GREEN**.
- [#42013597003](https://github.com/Iam-2squared/ark-ai/actions/runs/42013597003)
  Memory source and [#42013758662](https://github.com/Iam-2squared/ark-ai/actions/runs/42013758662)
  Memory source/test: **IN PROGRESS** at observed read.
- [#42014137117](https://github.com/Iam-2squared/ark-ai/actions/runs/42014137117)
  Planner source and [#42014289562](https://github.com/Iam-2squared/ark-ai/actions/runs/42014289562)
  Planner source/test: **IN PROGRESS** at observed read.
- [#42014752088](https://github.com/Iam-2squared/ark-ai/actions/runs/42014752088)
  redaction source: **IN PROGRESS**; final source/test
  [#42014890911](https://github.com/Iam-2squared/ark-ai/actions/runs/42014890911)
  **QUEUED** at observed read. Do not claim latest 6/6 GREEN.
- No workflows were manually re-run or duplicated. Every source/test write used
  ordinary Contents API and checked fresh PR HEAD. No alternate Git-object or
  ref-write safety bypass, force push or main merge.

## Explicit remaining work

1. Check exact-head full Ubuntu/Windows CI for Memory, Planner and redaction,
   repair actual failing expectations or code without weakening protection.
2. Audit Planner's `_checked_snapshot` callback return boundary: a patched
   `_snapshot` could replace a field descriptor after the pre-call check,
   before the first `result.tail` read. A post-callback
   `_require_original_recovery_denials()` before any result field access is
   a next isolated source change; do not overwrite an in-flight same-path CI.
3. Continue local Memory row/event/CAS/expiry coherence and read-only ambiguity
   without inferring retry authority. Only connect PermissionGate, registry,
   occurrence and audit-before-mock-action after exact-head dependency GREEN.
4. Preserve frozen V1/V2/Local UI/Launcher, PR #5 V3 Contract 1, and protected
   V2 final-evaluation boundaries. PR #5 and PR #9 remain Draft/unmerged;
   **ALL NEW UI/FRONTEND WORK PAUSED**. Read-only V3 pre-paid-compute audit
   still requires exact immutable base/tokenizer identity, real reviewed 120/30
   dataset, hardware/runtime/cost evidence and explicit authorization.
   No Candidate/adapter/weights, real GPU or other billable service, live tool,
   credentials, human review fabrication, irreversible cleanup or main merge.
   **ARK/JARVIS/V3 NOT_PASSED.**
