# ARK JARVIS Run591 — Local audit and Memory suffix-loss fail-closed guards

**Source audit at:** 2026-11-04T06:49:17.077+09:00 (ordinary process clock, not trusted time). **Work basis:** `8b8f37a8261b264448000dcf9d5beb31ec1146dd`; PR #8 Draft `research/jarvis-foundations`. No UI, main, PR #5, or protected-contract edits.

## Package A: audited append history admission

- Source `src/ark/agency/audit.py`, commit `554f6fc49753c0833d968481361c556a4a26d9a5`.
- Regression `tests/test_action_audit_append_sequence_run591.py`, commit `e25061a759b5402e34d88925dc84d31ed6b96db5`; six parameter-expanded synthetic cases.
- Within the same SQLite `BEGIN IMMEDIATE` writer transaction, admission now checks `COUNT/MIN/MAX(event_id)` against the `AUTOINCREMENT` `sqlite_sequence` high-water value. Reject missing first/middle events, deleted suffix, entirely deleted history, or an event-id jump before appending another audit row.
- No v1 DDL or contract changes, no backend dispatch, no untrusted action execution. Existing coherent, contiguous histories remain appendable, including restart at an equal supplied timestamp.
- Local high-water is **not independent historical evidence**: actors with SQLite write access can also rewrite the counter and rows. Retained independent witnesses and immutable external custody are separate unresolved requirements.

## Package B: read-only Memory v1 suffix-loss detection

- Source `src/ark/memory/sqlite_event_alignment.py`, commit `6d8044c5af94a8ae196e00a98300ed4397e2c178`.
- Regression `tests/test_memory_event_high_water_run591.py`, commit `b57a076306d6c62428e781cce5f7385ba350dc1d`; five synthetic cases.
- The existing complete row/event lifecycle scan already rejects first/middle `event_id` gaps. It now also verifies `sqlite_sequence` for `memory_events` **inside the same read transaction**. Deleting the last event together with its live row, or removing the entire history, must not be classified as an empty or shorter coherent history merely because surviving event IDs remain dense.
- Missing or corrupted local high-water is rejected. Valid CREATE/UPDATE/DELETE chronology remains readable. This is read-only, not an erasure proof, authenticated actor identity, consent, or a guarantee against coordinated row+counter rewriting.
- Memory's frozen v1 schema and interfaces remain unchanged. No protected V2 evaluation opened.

## CI / qualification / safety

- Prior exact-head `8b8f37a8261b264448000dcf9d5beb31ec1146dd` [run #41716782114](https://github.com/Iam-2squared/ark-ai/actions/runs/41716782114): completed SUCCESS, six Python 3.11–3.13 Ubuntu/Windows jobs PASS. This is **pre-change evidence**, not this run's PASS.
- [Audit source CI #41724289504](https://github.com/Iam-2squared/ark-ai/actions/runs/41724289504) and [audit-test CI #41724375903](https://github.com/Iam-2squared/ark-ai/actions/runs/41724375903): IN PROGRESS when sampled; audit-test Ubuntu 3/3 GREEN, Windows still running.
- [Memory source CI #41724520389](https://github.com/Iam-2squared/ark-ai/actions/runs/41724520389) and [Memory-test CI #41724604653](https://github.com/Iam-2squared/ark-ai/actions/runs/41724604653): IN PROGRESS when sampled; Memory-test Ubuntu 3.12 GREEN, remaining jobs not final.
- **11 authored test cases** are not independent locally executed pytest passes. This environment cannot clone the repository directly; full exact-head CI is the qualification gate. No duplicate manual CI reruns.
- No paid external compute/GPU/API, candidate creation, credentials, real ToolBackend, notification, automatic replay, data erasure or merge. PR #5/#8/#9 remain Draft; UI work remains paused; ARK/JARVIS/V3 **NOT_PASSED**.

## Next plan / 今後の方針

1. Verify latest exact-head Windows+Ubuntu 6/6 CI; diagnose failures from job logs and use only the normal source/test GitHub write path for minimal repairs.
2. Independently retained Memory CAS / unknown COMMIT review and Planner FAILED/BLOCKED restart recovery; avoid interpreting synthetic SQLite self-checks as external custody.
3. Registry-bound Tool identity, exact-type PermissionGate, persistent one-shot authorization, audit-before-action and unknown-outcome quarantine; maintain disconnected/mock backend boundary.
4. Personal Context revocation, proactive duplicate fencing, observation fixture contracts, free-only V3 provenance and approval/path guards. Do not touch paused UI or frozen evidence.
