# Run1407 — PlannerJournal lookup-hook absence custody

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `36368ccc4160727c79fb24704a675d589575b414`.
- Child branch: `research/run1407-planner-journal-hook-absence-custody-20261125`.
- Child HEAD before this evidence document: `371bb35d1f196a4b93349392f73fa4dd8e4635d5`.
- Source: `src/ark/agency/planner_journal.py`.
- Regression test: `tests/test_planner_journal_hook_absence_custody_run1407.py`.

## Finding and correction

The PlannerJournal path guard used `vars(type).get("__getattribute__") is not None` and the same check for `__getattr__` to represent absent class lookup hooks. Namespace lookup with `.get` returns `None` both when a name is absent and when it is explicitly installed with value `None`. The guard therefore accepted a changed class namespace even though the exact lookup policy had changed.

The guard now retains the exact hook-name vector, a unique absence sentinel, and the original per-hook descriptor vector in keyword-only defaults. It checks vector/sentinel identity, namespace membership, and descriptor identity before reading instance path state. Explicit `None`, the sentinel itself, sentinel replacement, and equal-valued vector replacement are denied.

## Regression coverage

- Explicit `None` for `__getattribute__` and `__getattr__` is rejected.
- Installing the exact absence sentinel as a class hook is rejected.
- Replacing the absence sentinel is rejected.
- An equal-valued replacement hook-name tuple is rejected.
- Hostile lookup hooks are rejected before instance lookup executes.
- The original unmodified PlannerJournal hook policy remains accepted.

All tests use a temporary local SQLite journal and class-level monkeypatches only. No ToolBackend, executor, trusted clock, consent, or external effect is invoked.

## Scope and evidence limits

PlannerJournal v1 DDL, event/hash formats, path identity, CAS, terminal propagation, COMMIT-UNKNOWN behavior, recovery semantics, public APIs, and frozen contracts are unchanged. This is local in-process class-definition integrity only; it is not process isolation, atomic directory-handle custody, authenticated storage identity, fsync/power-loss proof, or exactly-once external-effect evidence.

No paid/external compute, paid service, Candidate generation/promotion, protected V2 evaluation, credential, hardware action, frozen-contract change, main merge, or UI/frontend work occurred. PR #5 and PR #8 remain Draft/unmerged; PR #9 remains untouched. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no PASS is claimed.
