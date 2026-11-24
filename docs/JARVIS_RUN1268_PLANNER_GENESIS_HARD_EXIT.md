# JARVIS Run1268 — Planner genesis native-COMMIT hard-exit regression

## Exact basis

- Repository: `Iam-2squared/ark-ai`.
- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `64d5609a0c09ce789f3d19211ad6610839690929`.
- Test-only package; no Planner production source, schema, journal event format, public API or frozen contract changes.

## Regression coverage

- Initialize the existing local Planner journal schema.
- A spawned process creates a synthetic one-step plan through production `PlannerJournal.create_plan`.
- A connection wrapper delegates the native SQLite `COMMIT`, then exits immediately with `os._exit` before connection cleanup or receipt return.
- A cold `PlannerJournal` instance must recover the committed genesis row at sequence 0 with the exact all-PENDING graph.
- Require no ambiguous RUNNING steps, dispatch authority or automatic replay authority.
- Verify SQLite quick-check, one exact genesis metadata row, zero transition events, and absence of raw synthetic ToolCall arguments from the database and any surviving SQLite sidecars.

## Evidence boundary

This complements the existing genesis COMMIT-acknowledgement-loss test and terminal-transition hard-exit test. It specifically covers successful native COMMIT followed by abrupt process termination before Python cleanup/caller return. It is synthetic local SQLite process-exit evidence only, not fsync/power-loss certification, filesystem durability certification, trusted time, execution authorization or exactly-once external effects.

No ToolBackend is invoked and no live personal data is used. No paid/external compute, Candidate generation/promotion, protected V2 evaluation, credentials, hardware, destructive operation, frozen-contract change, UI/frontend work or main merge is performed. PR #5/#8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no local pytest/Ruff PASS is claimed.
