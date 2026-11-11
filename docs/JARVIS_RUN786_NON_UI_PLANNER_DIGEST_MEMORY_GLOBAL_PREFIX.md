# ARK JARVIS — Run786 / 2026-11-11 JST

**FREE-ONLY / NON-UI / SYNTHETIC / NOT_PASSED.** This is source-grounded
engineering evidence, not approval, independent custody, a real model test, or
permission to execute tools.

## Package A — detached Planner canonical state integrity

A caller-held `SyntheticPlanRecovery` could previously contain structurally
valid, but modified, `step_statuses` while retaining its original
`tail.status_digest`. Its comparison was classified as ordinary drift.
`src/ark/agency/disconnected_planner_epoch_recheck.py` now recomputes the
same local canonical `pstate_` state digest as the journal's `PlanGraph`
and rejects mismatched snapshots **before local journal recovery**. It also
requires PENDING to have revision zero and every non-PENDING state to have a
positive revision; legitimate terminal and cascaded BLOCKED states remain
supported. Reentrant carrier changes during digest construction are refused.

New `tests/test_planner_detached_status_digest_run786.py` provides seven
cases: three valid-grammar tamper images, three impossible state/revision
images, and legitimate previously retained RUNNING -> later SUCCEEDED drift.
The result remains read-only `MATCH_AT_READ`/`DRIFT_AT_READ`; it cannot
authorize dispatch, grant a write lease, or prove freshness after return.

## Package B — selected Memory scopes with an optional global retained witness

A selected-owner snapshot's global event count/sequence check did not
authenticate the **payload** of an unselected owner's event. The separate
`sqlite_event_prefix_review.py` already defines an independently *caller-
retained* global prefix format. The optional `retained_global_prefix`
parameter to `review_synthetic_memory_scopes()` now checks the prior
global prefix bytes within the **same SQLite WAL read transaction** as
global high-water and selected scoped rows. This is a compatibility-preserving,
strictly optional local witness: unchanged selected-owner snapshots survive a
legitimate append by another owner, while foreign payload rewrites and a
coordinated local suffix/sequence rollback are rejected when old witness bytes
are available.

New `tests/test_memory_scoped_retained_global_prefix_run786.py` has five
parametrized tests: two foreign-event payload modifications, allowed append,
coordinated event-tail+sqlite_sequence rollback, and invalid retained prefix
types. Test SQLite files are disposable, not user data. Neither the local
prefix digest nor its caller-provided custody establishes historical author,
trusted time, independent external storage, deletion proof, or consent.
A coordinated edit of local DB and external witness remains outside scope.
No Memory v1 schema change, live-memory ingestion, auto-repair, or real action.

## Exact branch, commits and evidence

- Initial work-basis branch `research/jarvis-foundations`, Draft PR #8,
  HEAD `5664c3c848566475010967d0f84f8c3a434b7340`.
  Baseline [#42969314891](https://github.com/Iam-2squared/ark-ai/actions/runs/42969314891)
  is **COMPLETED/SUCCESS** with six individually verified Windows/Ubuntu
  Python 3.11/3.12/3.13 jobs.
- Planner source `8ffb0110543e935ac2e5bbe5397e96d9af53c3c7`;
  Memory source `6d56610934902ca24d3eeb3f88e56ca0c1f0bf67`;
  Planner regression tests `b21ccfd1e5a1fd171c752b747aad6f52d76dc3aa`;
  Memory regression tests `2115fe935da24ad7c00ca605c20e54635d33f1da`.
- Actual CI on the intermediate Memory source/test snapshots
  [#42974676407](https://github.com/Iam-2squared/ark-ai/actions/runs/42974676407),
  [#42974753427](https://github.com/Iam-2squared/ark-ai/actions/runs/42974753427)
  and [#42974800733](https://github.com/Iam-2squared/ark-ai/actions/runs/42974800733)
  revealed Ruff `I001` import ordering defects, not an authorization test failure.
  Normal-Contents repair commits: source `71b8a4cd2e9a8aca59f430d586ffa79e8188d607`,
  test `71e1f0835c5c436f603e2849d4463109cf47eac8`.
  **Latest source/test six-job GREEN was not established at report
  preparation; do not borrow successes from earlier hashes.**
- The new tests are **submitted**, not declared PASS until matching
  GitHub Actions results can be inspected. No duplicate manual workflow
  was triggered. No local full-suite or physical-PC verification claimed.

## Authorization/freeze and next plan

Only non-UI ARK core files and disposable synthetic tests were changed.
PR #5 protected V3 final gate and PR #9 paused UI remain Draft/unmerged and
untouched, as do main, frozen V1/V2/Local UI/Launcher contracts, evaluation
evidence and Candidate artifacts. No paid API, GPU, external tool, real
microphone/camera, new credentials, training, model promotion, irreversible
action, force-push, or main merge.

Next: verify the latest six CI jobs; correct only evidenced failure, then
strengthen original global-prefix helper custody before reading private
event payloads, and continue retained-epoch/COMMIT-UNKNOWN manual recovery.
Planner may be integrated with PermissionGate/audit/mocks **only after**
lower-level exact-HEAD GREEN and no real dispatch is enabled.
