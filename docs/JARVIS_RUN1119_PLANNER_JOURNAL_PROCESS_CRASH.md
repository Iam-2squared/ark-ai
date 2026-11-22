# Run1119 — Planner journal terminal-transition process-crash boundary

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Parent HEAD at branch creation: `e0bbe9635f232e1fd1a897024ade9059426eb3f9` (after Run1118 Memory and Personal Context integrations).
- Child branch: `research/run1119-planner-journal-process-crash`.
- Test: `tests/test_planner_journal_process_crash_terminal_run1119.py`.

## Coverage

- Establish a synthetic PlanGraph with a root step in RUNNING and one dependent step.
- Spawn a fresh Python process that attempts the terminal RUNNING → FAILED transition.
- Hard-exit immediately before native SQLite COMMIT, then cold-reopen and require RUNNING to remain ambiguous with no automatic retry.
- Hard-exit immediately after native SQLite COMMIT, then cold-reopen and require FAILED plus dependent BLOCKED.
- Verify exact durable event sequence, retained earlier tail, SQLite quick_check, and both dispatch/replay authority flags remain false.

## Limits

This is a local synthetic crash fixture for the replay-only Planner journal. It does not dispatch a ToolBackend, grant permission, prove external exactly-once effects, provide trusted time, or authorize automatic retry. Planner journal schema/hash-chain/transition semantics and frozen contracts are unchanged. No UI, paid/external compute, Candidate, protected V2 evaluation, credentials, hardware action or main merge is included.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no PASS is claimed until that run is GREEN.