# Run1155 — Planner COMMIT recovery rebase

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `9b1dbc439ec338e2840d9dc493e724c651617e60`.
- Rebased from Draft PR #339 exact child HEAD: `7b07253ec587ef458aac5adad00b7c00c7d77a51`.
- Source exact-head CI: [45115302796](https://github.com/Iam-2squared/ark-ai/actions/runs/45115302796) GREEN, 6/6 on the source head only; it does not transfer to this rebase.
- New child branch: `research/run1155-planner-permission-rebase-latest`.
- Test: `tests/test_planner_journal_commit_unknown_run1149.py`.

## Coverage

The subprocess regression injects a lost SQLite COMMIT acknowledgement into `SyntheticPlanJournal.append` and exercises both possible storage outcomes:

1. The event and header update commit durably before the acknowledgement is lost.
2. The transaction rolls back before the acknowledgement is lost.

Cold recovery verifies atomic event/header state. A durable RUNNING transition remains ambiguous and non-replayable; stale genesis CAS is rejected. A rolled-back transition leaves the original PENDING state and zero events. The injected boundary confirms exactly one COMMIT attempt in both cases.

The SQLite factory is patched before importing the Planner journal and is armed only for the exact append read/write URI. The test uses disposable local SQLite and an inert synthetic ToolCall.

## Evidence boundary

Test-only. No Planner production source, schema, transition policy, or execution authority changes. This does not prove fsync/power-loss durability, independent storage custody, trusted time, authenticated provenance, consent, real ToolBackend execution, or exactly-once external effects. No automatic replay or external dispatch is added.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required before any PASS claim. No local pytest/Ruff result is claimed. PR #8 and PR #5 remain Draft/unmerged; PR #9 remains untouched; ARK/JARVIS remains NOT_PASSED.
