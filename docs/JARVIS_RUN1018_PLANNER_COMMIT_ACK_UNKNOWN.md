# ARK AI Run1018 — Planner COMMIT acknowledgement loss

**Work basis:** Draft PR #8 branch `research/jarvis-foundations`, exact HEAD `40c3467d6e45c477780f1c83b2a1cfa53111f932`. This is a test-only child; the parent remains OPEN/DRAFT/UNMERGED.

## Finding

The disconnected Planner journal already has post-COMMIT callback-failure, hard-exit, restart quarantine and terminal DAG propagation coverage. The new tests target the lower-level SQLite acknowledgement boundary directly: the native COMMIT succeeds, then the caller receives an injected `sqlite3.OperationalError` instead of a transition result.

## Regressions

Two synthetic cases use a proxy around only the disposable Planner SQLite connection:

1. A lost acknowledgement after a `RUNNING` commit must cold-recover as ambiguous `RUNNING`, with no dispatch or automatic replay. The original expected revision cannot append a duplicate transition.
2. A lost acknowledgement after a terminal `FAILED` commit must cold-recover the terminal state and block its dependent child, while leaving an independent step pending. The old terminal revision cannot replay the transition.

Both cases verify the exact durable event rows and SQLite `quick_check`. The tests are authored; no local pytest PASS is claimed. Exact-head Windows/Linux × Python 3.11–3.13 CI is required.

## Limits

Synthetic PlanStep/ToolCall descriptions and disposable local SQLite only. This does not execute tools, prove external outcomes, provide authenticated writer provenance, trusted time, independent custody, power-loss/fsync durability, exactly-once external effects or automatic retry authority. No real ToolBackend, paid service, external compute, credentials, live personal data, Candidate, protected V2 evaluation, frozen contract, UI, PR #5, PR #9 or main branch is changed.
