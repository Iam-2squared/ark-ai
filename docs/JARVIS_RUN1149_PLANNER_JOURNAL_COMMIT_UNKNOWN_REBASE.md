# Run1149 — Planner journal ambiguous COMMIT outcome

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Parent work-basis HEAD: `1f809e6489584ca0d4cc3b9291995696216c53bf`.
- Child branch: `research/run1149-planner-journal-commit-unknown`.
- Test: `tests/test_planner_journal_commit_unknown_run1149.py`.

## Coverage

The subprocess regression injects a lost SQLite COMMIT acknowledgement into `SyntheticPlanJournal.append` and exercises both possible storage outcomes:

1. The event and header update commit durably before the acknowledgement is lost.
2. The transaction rolls back before the acknowledgement is lost.

The test then opens a cold journal and verifies that the event row and header frontier remain atomic. A durable RUNNING transition is recovered as ambiguous, never automatically replayed, and a stale genesis revision is rejected. A rolled-back transition leaves the original PENDING state and zero events. The injected boundary confirms exactly one COMMIT attempt in both cases.

The SQLite factory is patched before importing the Planner journal and is armed only for the exact append read/write URI. The test uses disposable local SQLite and an inert synthetic ToolCall.

## Evidence boundary

This is a local journal COMMIT-ambiguity regression. It does not prove fsync/power-loss durability, independent storage custody, trusted time, authenticated provenance, consent, real ToolBackend execution, or exactly-once external effects. No Planner production source, schema, transition policy, or execution authority changes. No automatic replay or external dispatch is added.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required before any PASS claim. No local pytest/Ruff result is claimed. PR #8 and PR #5 remain Draft/unmerged; PR #9 remains untouched; ARK/JARVIS remains NOT_PASSED.
