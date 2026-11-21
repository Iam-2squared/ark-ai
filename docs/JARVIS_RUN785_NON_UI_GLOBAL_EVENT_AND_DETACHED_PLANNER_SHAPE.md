# ARK JARVIS Run785 — global Memory journal high-water & detached Planner image grammar

Date: 2026-11-11 JST. **FREE-ONLY / NON-UI / SYNTHETIC / NOT_PASSED.**

## Why the changes matter

1. **Scoped Memory snapshots previously inspected only selected namespaces.**
   A caller asking about owner A could obtain a locally coherent snapshot even
   after a record *and its terminal event* belonging to owner B disappeared.
   The new read-only check compares global `COUNT/MIN/MAX(event_id)` with the
   single `sqlite_sequence` high-water row **inside the same SQLite WAL read
   transaction** used to inspect the requested scopes. A missing first/middle/
   tail event or duplicate high-water marker now fails closed before the
   per-scope event and row replay. It does **not** inspect or authenticate the
   payload of unselected owners' events. It cannot detect a coordinated rewrite
   of both SQLite tables and their high-water without independently retained
   earlier evidence. No v1 schema, write operation or disclosure API changed.

2. **Detached Planner recovery images need an exact status grammar.**
   The read-only `recheck_disconnected_planner_epoch` accepted a detached
   recovery image whose tuples had correct broad Python types but invalid
   values (unknown state strings, boolean/negative/overflow revisions,
   duplicate/unsorted step identifiers or inconsistent ambiguous-RUNNING
   markers). Such malformed input must not become an ordinary `DRIFT_AT_READ`
   diagnostic. It is now rejected before journal recovery. Valid step IDs
   retain the original nonempty exact-text contract (no invented 128-character
   bound). The real recovered RUNNING snapshot remains `MATCH_AT_READ` only,
   never a WRITE lease or permission to replay.

## Exact source / tests

Work basis: `research/jarvis-foundations` HEAD
`2a0fcdcece8cf9f7ceeead304c717d7cad7c9e68`, previously verified on
GitHub CI [#42961963086](https://github.com/Iam-2squared/ark-ai/actions/runs/42961963086)
with six completed successful Windows/Ubuntu × 3.11/3.12/3.13 jobs.

- Memory implementation `src/ark/memory/synthetic_multiscope_integrity_review.py`
  at `21e45312289ceb25f660a56c6adaf9696d004edb`; four regressions in
  `tests/test_memory_multiscope_global_highwater_run785.py` at
  `b6be0fe9f48d9dee817d13733a7195e0c2cd7df6`.
- Planner implementation `src/ark/agency/disconnected_planner_epoch_recheck.py`
  at `e683fdd651bb2458f1ffbb628d4ee48c45552608`; compatibility correction
  `b6c8d020579e0244229031a9203f331af4a678a0`; ten regressions in
  `tests/test_planner_detached_recovery_shape_run785.py` at
  `69afdc68e90117428f64b215ea45ade226a974d8`.

**Fourteen new parametrized tests submitted to GitHub CI; new exact-head
six-job success was not yet established when this report was prepared.**
No local full-suite/GGUF or external hardware execution claim is made.
CI naturally runs on each ordinary Contents commit; no manual duplicate run
was launched. Interpret CI only against its exact source/test SHA.

## Read-only audit of independent existing controls

Inspected the existing `sqlite_event_alignment.py` and
`atomic_epoch_review.py` global high-water logic: they already validate
local append order. This package closes the same gap in the *separate* scoped
snapshot reviewer; the stronger full-history and retained-prefix reviewers
remain independent. The Planner detached status checks are input validation;
they neither change the frozen `SyntheticPlanJournal` DDL nor promise
cross-SQLite atomicity, external exactly-once effects, authenticated consent,
or trusted clocks.

No UI/frontend files, protected V1/V2/Local UI/Launcher contracts, V3
Candidate weights/adapters, protected evaluation, physical device, actual
backend dispatch or notification, paid service, or default branch were touched.
PR #5 stays Draft/unmerged, and PR #9 stays Draft/unmerged and untouched.

## Next plan / 今後の方針

1. Establish the latest source/test HEAD's exact six-job CI result and repair
   only evidenced regressions, without overwriting concurrent branch work.
2. Continue Memory cross-owner rollback witness and post-COMMIT-UNKNOWN
   diagnostics with independent retained evidence; keep recovery manual.
3. Complete Planner terminal-state/restart invariants, then separately
   connect immutable registry, exact PermissionGate, trusted-clock audit-before-
   action and disconnected mock fixtures **only after exact-head GREEN**.
4. Extend privacy-safe Personal Context and occurrence/observation backend
   contracts while keeping new UI development paused.

Completion verdict: **ARK / JARVIS / V3 NOT_PASSED**.
