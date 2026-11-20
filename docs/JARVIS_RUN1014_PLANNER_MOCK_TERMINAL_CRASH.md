# Run1014 — Planner/mock terminal COMMIT hard-exit boundary

## Work basis and dependency evidence

This is a test-only child of Draft PR #22 exact head `8dd522befb15e39b805a417744dd2fc89db49331`, whose exact-head CI run [#44560895025](https://github.com/Iam-2squared/ark-ai/actions/runs/44560895025) completed GREEN.

Relevant independently validated lower-level evidence includes:

- Draft PR #51 Planner journal hard-process COMMIT tests, exact head `9ce928b87b5d69d0cf5ae23f137d769d49552a53`, CI [#44669861991](https://github.com/Iam-2squared/ark-ai/actions/runs/44669861991) GREEN.
- Draft PR #43 occurrence commit-crash boundary, exact head `67426ce2de9f0d70a848d83018deb258823a90fc`, CI [#44648800414](https://github.com/Iam-2squared/ark-ai/actions/runs/44648800414) GREEN.
- Draft PR #45 pre-action audit commit-crash boundary, exact head `96c1816bda46e35c1777c4610a6e5ed1890f4a1d`, CI [#44656403662](https://github.com/Iam-2squared/ark-ai/actions/runs/44656403662) GREEN.

This child adds no production source. It tests the remaining composition boundary after the mock executor has returned but before the Planner's terminal SUCCEEDED transition is known to the caller.

## New regression

A spawned process executes one synthetic registered WRITE through the durable Planner/mock cycle. The test intercepts only the Planner journal's third COMMIT: constructor bootstrap/schema is COMMIT #1, the RUNNING transition is COMMIT #2, and terminal SUCCEEDED is COMMIT #3.

- **Before native terminal COMMIT:** terminate the process before COMMIT #3 (terminal SUCCEEDED) commits. Cold recovery must retain RUNNING as ambiguous.
- **After native terminal COMMIT:** terminate immediately after SQLite reports COMMIT #3 (SUCCEEDED), before the transition receipt can return. Cold recovery must report SUCCEEDED.

In both cases the independent synthetic occurrence reservation and the two local audit events already exist. A fresh process-local gate/backend must not retry the step; the backend call count remains zero in the retry process and the persisted audit/occurrence state remains unchanged.

## Interpretation and limits

This is local SQLite process-termination evidence for a disconnected mock. It does not prove power-loss/fsync durability, cross-store atomicity, trusted time, consent, independent custody, external backend identity, or exactly-once real-world effects. The mock completion audit is not evidence of an external effect. RUNNING remains quarantined; SUCCEEDED reflects only the local mock cycle.

No real ToolBackend, hardware, model, live personal data, paid service, external compute, credentials, Candidate artifact, frozen contract, UI code, protected V2 evaluation, PR #5, PR #9, or main branch is changed.

The test-bearing exact head `7b4ce4809e33b699061a69bd7963f07defd65d6c` passed exact-head CI run [#44690231075](https://github.com/Iam-2squared/ark-ai/actions/runs/44690231075) GREEN 6/6. This documentation correction creates a new head and requires its own exact-head CI; no PASS is claimed for that new head.
