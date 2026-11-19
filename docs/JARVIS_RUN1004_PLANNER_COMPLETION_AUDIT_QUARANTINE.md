# Run1004 — Planner quarantine after post-mock completion-audit failure

**Work basis:** Draft PR #22 exact head `8dd522befb15e39b805a417744dd2fc89db49331` (CI #44560895025 GREEN 6/6). This test-only child targets PR #22; the lower-level registry, PermissionGate, occurrence, audit, journal and mock-composition source is unchanged.

## Gap covered

The existing Planner/mock composition test covered a pre-action audit failure, where the backend must not run. It also covered uncertain Planner terminal persistence. This fixture covers the distinct interval after the exact mock backend has returned but before the completion-audit append succeeds.

## Regression

A synthetic audit clock succeeds for the pre-action event and raises on the second sample. The test requires:

- exactly one mock backend call;
- only the durable `mock_pre_action` audit event;
- the Planner journal remains at its durable RUNNING sequence;
- recovery classifies the step as ambiguous and non-ready;
- a restart attempt is rejected before another backend or audit call.

This is local failure-injection evidence only. The synthetic backend has no external effect and the clock callback is not a trusted clock.

## Safety and limits

No production source, real ToolBackend, real WRITE, live notification, external service, paid compute, credential, model, Candidate, frozen contract, V2 evaluation, UI branch or main branch is changed. Separate SQLite stores remain non-atomic. The test does not prove exactly-once external effects, trusted time, authenticated consent or independent custody.

**Exact-head CI is pending until this child PR is opened; no PASS is claimed. PR #22 remains Draft/unmerged. Overall ARK/JARVIS remains NOT_PASSED.**
