# ARK AI — Run640 / Non-UI core, deterministic Memory model, and checkpoint history custody

## Scope and work basis

- Run basis: Draft PR #8 `research/jarvis-foundations` at `716a6ba6f20e2fa35602c5f9b1f6faa61dcf6104`; previous exact-head [Actions #42079747077](https://github.com/Iam-2squared/ark-ai/actions/runs/42079747077) **GREEN on all six** Ubuntu/Windows × Python 3.11–3.13 jobs, observed this invocation.
- Read-only gate checks: PR #5 and PR #9 remain Draft/open and unmerged; the existing UI branch has not been modified.
- No new UI/frontend code, external models, paid services, protected evaluation, actual tool execution, device access, credentials, grants, promotion, destructive user-data operations, or main merge.

## Package A — Disconnected observation carrier contract preaccess

- Source: `src/ark/observation_fixture_chain_review.py`, commit `435272d90039e9e02854434499a9103809361e35`.
- Regression: `tests/test_observation_chain_original_carrier_custody_run640.py`, commit `d6f7ae8d03649884c4d184eddabfa96419c32c15` (15 authored definitions).
- Before reading caller-supplied fixture metadata, reject substituted `ObservationEnvelope` field slots, lookup hooks, and validator method. Before creating a digest-only result, reject substituted result initializer/field slots/lookup hooks; keep original False-only denial flags. Tests use benign synthetic text and do **not** replace the `__new__` method on any existing Python class.
- This review establishes only local closed-chain consistency; it cannot authenticate media capture, source provenance, retention, consent, or dispatch.

## Package B — Multi-scope Memory lifetime/CAS model

- Regression: `tests/test_memory_multiscope_generation_model_run640.py`, commit `b599759ed2c5e296943e74ed6264b59b38822c69` (three deterministic seeds, 48 bounded steps per seed).
- Exercises two SQLite handles, multiple isolated MemoryScope/source identities, fresh and repeated generations, opt-in generation-fenced updates, stale token denial, deletion and recreation, and read-only global row/event alignment after every committed synthetic mutation.
- Tests write/delete **only disposable pytest tmp_path databases**. No frozen Memory v1 API/DDL or production write semantics changed; a CAS token remains non-authorizing. The step count is deterministic, not a benchmark.
- Three cases are **authored**, not evidence of a pytest pass until matching CI succeeds.

## Package C — Canonical checkpoint growth and verbatim historical preservation

- Before this change, `docs/PROJECT_STATUS.md` held 1,043,400 characters in 4,540 lines, blob `e5dd32bd25d002d621bff5702224ebeef6561aa2`. A 1 MiB-scale canonical file makes Contents API update reliability and quick review increasingly fragile.
- Two **non-destructive** archive parts saved via normal GitHub Contents writes:
  - [Part 1](status_archive/PROJECT_STATUS_THROUGH_RUN639_PART1.md), commit `ab412fd4e847b13e265edb2180782261b47f44e0`, blob `98c268c1f3270bb007bd936f0fc49bb27ecc314c`, 526,563 JS characters.
  - [Part 2](status_archive/PROJECT_STATUS_THROUGH_RUN639_PART2.md), commit `2802a007a2d5b39e2dc063c0a14bd20dc08780a7`, blob `b9bcd7bf567990703e2b37ad73d27e174a9e5a4e`, 516,837 JS characters.
- A fresh GitHub fetch of **both saved archive parts** was concatenated and compared with the original full canonical text; the comparison was **exactly equal**, preserving every historical line and old result in order. The old blob remains in Git history, too.
- The canonical status can now be reduced to a short latest index at the **single end-of-invocation checkpoint update**. Archive parts are only history; they do not replace the live LATEST pointer. No frozen contracts/evidence were edited.

## Package D — Planner terminal and restart model

- Regression: `tests/test_planner_multibranch_restart_model_run640.py`, commit `c795309ed789223e1bd4d99391570ca9aa75fae0` (**2 parameterized tests authored**).
- Both FAILED and CANCELLED root outcomes block all pending descendants through restart, while an unrelated branch may finish normally. Every synthetic transition is replayed from a freshly constructed journal and compared with the saved receipt, retained-prefix integrity and ambiguous RUNNING witnesses are checked, and forbidden later transitions cannot append.
- No real ToolBackend is called, no journal schema/frozen contract changed, and no stale RUNNING/WRITE is authorized for automatic replay.

## Exact-head CI failure triage and corrections

- The source-only [CI #42087444443](https://github.com/Iam-2squared/ark-ai/actions/runs/42087444443), observation-test [#42087533753](https://github.com/Iam-2squared/ark-ai/actions/runs/42087533753) and later Memory-test [#42087980817](https://github.com/Iam-2squared/ark-ai/actions/runs/42087980817) each showed Ubuntu 3.11/3.12/3.13 **FAIL**. The source-only Ubuntu 3.11 log reported **16 failed / 9,102 passed / 1 skipped**; the Memory-test Ubuntu 3.11 log reported **16 failed / 9,120 passed / 1 skipped**. The 16 existing observation tests expected late callbacks or older exception messages, while newly pinned class/descriptor identity fails safely before those callbacks.
- Four normal GitHub Contents test corrections (no production safety checks relaxed): `tests/test_observation_chain_input_anchored_result_run590.py` commit `1b53daa1cdcca21639a253ace1dae658ab12fb14`; `tests/test_observation_chain_pregetter_denial_run611.py` `1f856e3bad012483ff2af22e9b9d5a485f64b3b7`; `tests/test_observation_fixture_chain_review_run585.py` `20fbdf67957511b968b53b0b364a3426448ae20f`; `tests/test_observation_fixture_label_ingress_run639.py` `5eafd1e73262a6ea068beaca745b169f9b888276`.
- The revised tests now expect preaccess refusal of swapped constructors/getattribute hooks, and malformed-label tests keep the ORIGINAL guarded validator installed while checking the original UTF-8/budget errors. These are **CI-found failures, not claimed solved** until a post-correction exact-head 6/6 CI proves it. No duplicate manual workflow runs.

## Validation and unresolved boundaries

- Local `git ls-remote` cannot resolve `github.com` in the execution container; no local Python pytest or Ruff PASS is asserted.
- The original Run639 exact-head CI is confirmed **6/6 GREEN**. The first Run640 change [#42087444443](https://github.com/Iam-2squared/ark-ai/actions/runs/42087444443), combined observation regression [#42087533753](https://github.com/Iam-2squared/ark-ai/actions/runs/42087533753), archive updates [#42087682748](https://github.com/Iam-2squared/ark-ai/actions/runs/42087682748) and [#42087752286](https://github.com/Iam-2squared/ark-ai/actions/runs/42087752286), and Memory state machine [#42087980817](https://github.com/Iam-2squared/ark-ai/actions/runs/42087980817) were **IN PROGRESS/QUEUED at initial reading**. CI is automatically triggered by Contents commits; no duplicate manual workflow dispatch.
- Neither the digest, sqlite_sequence, caller-supplied clock, nor the synthetic audit is independently authenticated. Unknown WRITE outcomes still require manual reconciliation; no automatic retry.
- If any exact-head job fails, read its logs, correct the smallest source/test issue using normal guarded Contents updates, then resume a non-conflicting lane. Never treat earlier HEAD GREEN as latest HEAD GREEN.

## Priority after Run640

1. Confirm exact-head six-platform CI and fix only actual failures.
2. Expand Memory row/event/CAS expiry coherency and Planner durable terminal recovery, then integrate registry-bound PermissionGate and audit-before-action only after lower-level exact-head GREEN.
3. Maintain Personal Context privacy/readiness and proactive/observation fixtures; inspect free V3 gate/identity/path reproducibility without opening protected evaluation or spending.
4. Keep PR #5/#8/#9 Draft/unmerged, UI paused, main/frozen evidence unchanged and ARK/JARVIS/V3 **NOT_PASSED**.
