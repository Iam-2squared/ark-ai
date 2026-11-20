# Run1011 — Planner journal hard-process COMMIT boundary

**Work basis:** Draft PR #30 exact head 0857045761bb50c7d1549025c5fa7959af6e95f5, whose exact-head CI run #6598 completed GREEN across all six Windows/Ubuntu × Python 3.11–3.13 jobs.

**Isolated branch:** research/planner-journal-hard-exit-run1011, based on PR #30. PRs #18–#20 and #30 remain Draft/unmerged.

## New regression coverage

The new test tests/test_planner_journal_hard_exit_run1011.py launches a child process and terminates it at the actual SQLite COMMIT boundary for both Planner genesis creation and a RUNNING transition:

- **Before COMMIT:** the child exits after the transaction writes but before SQLite receives COMMIT. Cold reopen must discover that genesis or transition was not committed.
- **After COMMIT:** the wrapper calls the real SQLite COMMIT and immediately invokes os._exit before the journal method can return. Cold reopen must discover the committed genesis or transition.
- The four parameterized cases verify metadata/event row counts, the metadata sequence frontier, and SQLite quick_check.
- A committed RUNNING transition remains ambiguous, is not ready, and does not authorize dispatch or automatic replay. Reusing the pre-crash graph/sequence is rejected.
- No retry is performed after the uncertain caller outcome.

This complements Run996's in-process lost-COMMIT-acknowledgement tests and Run1003's pre-COMMIT rollback fault injection. It specifically tests operating-system process termination rather than a Python exception path.

## Safety and limits

Only synthetic PlanStep/ToolCall values, a disposable local SQLite database, and local subprocesses are used. No tool backend is called, no real action is inferred, and no external side effect is attempted. No Planner source, schema, DDL, transition policy, frozen contract, Memory, ToolRegistry, PermissionGate, UI, V2/V3 evaluation, or main branch is changed.

This is a process-death recovery test, not a power-loss/fsync guarantee, storage anti-rollback proof, trusted-time proof, cross-store atomicity guarantee, or external-effect receipt.

## Validation status

The test and this report are saved on the isolated branch. Exact-head CI starts after the Draft child PR is opened. No PASS is claimed before all six matrix jobs complete successfully.
