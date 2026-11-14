# Run603 — Non-UI WRITE uncertainty and recovery result authority

Scope: Draft PR #8 `research/jarvis-foundations`; no UI, main, frozen-contract or V3-Candidate changes. Work-basis checkpoint `164e1af7708b679540b0ed84cccfdf32f017c77a`.

## Findings and concrete changes

1. **Restore lint gate without security predicate changes.** The Run602 checkpoint CI `41802865339` failed Ruff E501 in three older tests because a previous fail-closed diagnostic update lengthened six `pytest.raises(match=...)` lines beyond 100 columns. Replace the six single-line contexts with line-wrapped equivalents; preserve the same exception classes, match patterns and assertions. Commits: `d37d365bc8b1cad90f6f56990ca626f9f43d1c84`, `81cb4729b9b68d11ea354f8b8168953ebc686e01`, `4148523ba3ac29e8ac42097ed8dd6824e6e448ee`.

2. **Quarantine matrix, before interpreting independent cross-store WRITE observations.** `src/ark/agency/synthetic_write_quarantine_matrix_review.py` stores the original exact result types and deny-only class descriptors at module import, and checks static identity at entry, across result/fixture callbacks and before returning a local digest. A counterfeit property returning `False` (or raising / mutating state from its `__get__`) is rejected **without invocation**. Tests `tests/test_write_quarantine_static_denial_getters_run603.py`: 4 denial flags × 2 mutation times (preinstalled or digest callback), plus one untouched positive (9 authored pytest cases). Source commit `c55e9bf360f26994c7e85a5522ae2e860a3ea151`; test commit `8a726d3b27c62f5057d6739f8a1a4166462a84a7`.

3. **Direct synthetic WRITE restart triage.** `src/ark/agency/synthetic_recovery_triage.py` pins all three original denial descriptors of `SyntheticRecoveryReview`, refusing substituted properties before opening source data, after diagnostic callbacks and before returning its witness. Even a syntactically valid recovery report cannot authorize dispatch, replay or claim an externally verified outcome. Tests `tests/test_recovery_deny_only_getters_run603.py`: 3 properties × 2 mutation times (preinstalled / after audit continuity callback), plus one untouched positive (7 authored pytest cases). Source commit `24c89dfafb575d8e5449569be6c382dfba84f590`; test commit `b260705dda28261af3581a9fda5561f9954ace30`.

## Memory retained alignment static authority (independent package)

4. **Coherent local Memory retained comparison is diagnostic-only.** The existing
   `src/ark/memory/sqlite_alignment_retained_review.py` comparison now validates
   import-pinned deny-only class descriptors for the retained
   `MemoryEventAlignmentReview` and returned
   `RetainedMemoryAlignmentComparison` before a property getter can run.
   It checks the same authority boundary before and after the source
   reconciliation callback and report construction. This is not proof of
   independent custody, historical writer identity or real consent.
   Source commit `767a1fed04376effc0f871f30f4aee2490f3be28`.
   `tests/test_memory_retained_alignment_original_denials_run603.py`
   contains **16 parameterized negative** preinstalled/late-change scenarios
   (8 properties x 2 times) plus **one normal nonauthorizing case**.
   Test commit `bb500bb876f59db352fcbc2cb82e98f460c52f29`.
   Total new authored Run603 regression cases: **33 (9 + 7 + 17)**;
   this number is NOT local pytest PASS evidence.

## Actual CI failure and response

At early recovery-source HEAD `24c89dfafb575d8e5449569be6c382dfba84f590`,
CI [#41810011869](https://github.com/Iam-2squared/ark-ai/actions/runs/41810011869)
reached Ubuntu 3.12 pytest with **7,993 PASS, one SKIP, five FAIL**.
All five failures were in existing
`tests/test_triage_result_epoch_run428.py` and expected a substituted
result constructor to be *called* before rejection. Static descriptor
identity validation now intentionally rejects that substitution **before
any constructor or registry callback**. Commit
`99731ca1315d2f036b384d0624aba4e0ce621161` updates the five test
assertions to require **zero** substituted constructor calls, **zero**
registry bind calls and **zero** backend dispatch calls. No production
gate was relaxed, no test was skipped or removed. CI after this correction
must be observed on its exact source head before any GREEN claim.

- The corrected old-test HEAD `99731ca1315d2f036b384d0624aba4e0ce621161`,
  workflow [#41810490156](https://github.com/Iam-2squared/ark-ai/actions/runs/41810490156),
  reached Ubuntu 3.12 **8,002 PASS, 1 SKIP, 3 FAIL**. The three new
  `test_recovery_deny_only_getters_run603.py` cases observed a substituted
  recovery property `__get__` run after an audit continuity callback;
  the call was denied, but the stricter **no-getter execution invariant
  failed**. Commit `5236bba4d6e7e3712d7bfa0b05893bb5e489e7a9` adds the
  original-descriptor recheck at each direct recovery `assert_epoch()`
  boundary, immediately following SQLite and registry callbacks. This is a
  production safety fix, **not** a relaxation of the test or denial rule.
  Subsequent exact-head CI must verify that no hostile getter runs.

## Evidence interpretation

- These **33 tests are authored test definitions, not 33 independently executed local pytest PASS**. CI for the exact post-change head must complete before a full GREEN claim. The preceding Run602 checkpoint failed on Ruff, not a validated pytest result.
- The quarantine and restart modules remain disconnected, offline diagnostic-only reviews. They do not open or modify real external services, grant permissions, change planner state, call ToolBackend.execute, certify trusted time or consent, or prove that a physical action happened exactly once.
- The four-database planner/reservation/audit/link observations are **separate local SQLite transactions**, not an atomic external-world snapshot. Even all-local-matching evidence cannot prove absence of a side effect, and there is no safe automatic retry of an unknown WRITE.
- Frozen V1/V2/Local UI/Launcher evidence and V3 approval/evaluation boundaries are not modified. PR #5 and PR #9 remain Draft/unmerged; UI development remains paused. The entire ARK/JARVIS completion gate remains `NOT_PASSED`.

## Follow-on integration gate

After exact-head six-job Ubuntu/Windows CI is GREEN: bind deny-only recovery and quarantine reports to a read-only startup observation surface with original source/witness identity; include mixed FAILED/BLOCKED/RUNNING Planner state, a missing-store fixture and a withheld-retry fixture. Do not connect real executors or introduce user approval semantics until their separate authorization and audit contracts are reviewed. Preserve manual-only reconciliation for ambiguous commits and write completions.
