# ARK AI Run946 — non-UI scope-isolated CAS, cold COMMIT-UNKNOWN triage, private mock receipts, terminal DAG isolation

## Scope and boundaries

This run adds only independent, reproducible synthetic test packages to the
already-implemented JARVIS foundations on Draft PR #8. No production
Memory/Planner/ToolRegistry/PermissionGate implementation was changed. The
completed implementation remains disconnected and reversible; no backend
dispatch, network/paid compute, GPU, owner approval, model training, or
physical-device action is authorized by these fixtures. ARK/JARVIS remains
**NOT_PASSED**.

## Authored packages

1. **Memory generation-fenced CAS / foreign appends** —
   `tests/test_memory_generation_foreign_append_run946.py`, commit
   `c9fbb89f339da447756ef4f8514a2511292a0b21`.
   Five scenarios place an unrelated SQLite event *after* observing a primary
   row's generation. They exercise distinct owner, distinct namespace,
   same-scope different source, foreign revision advance, and foreign
   deletion through a restarted handle. The retained primary token should
   still perform exactly one legitimate primary update, retain its original
   create-event lifetime, and leave global event IDs dense. This tests
   row-scoped fencing without wrongly treating the global append count as a
   one-row token. A local SQLite event chain is not independent custody.

2. **Atomic pre-action cold-process COMMIT-UNKNOWN** —
   `tests/test_atomic_unknown_cold_triage_run946.py`, commit
   `aff330da0c68cddc7ea20fc464e259b37132cddf`.
   Four retained-prefix/claim cases reconstruct the review inputs in a
   separate Python interpreter against a two-commit inert SQLite ledger.
   Classifications distinguish local presence, preexisting entries, foreign
   advancement, and unchanged tail while keeping dispatch, automatic replay,
   authenticated external-effect and independent custody all **False**.
   The outcome stays manual review regardless of local membership.
   Initial six-job CI `44117413077` rejected test-only import spacing
   (Ruff I001); normal GitHub Contents fix
   `e91e33e67c55f95939d2ca404f5dc588d95801cf`
   removes one blank line before the module constant. This is not a semantic
   change and does not relax review gates.

3. **Mock READ fixture privacy and denial** —
   `tests/test_disconnected_mock_privacy_receipt_run946.py`, commit
   `a82a97087ec41f2b6ff9559ce4675d6d7e3e3817`.
   Eight malformed-argument variants assert that a synthetic privacy sentinel
   is absent from exception text, exception repr and request repr. Four valid
   math, text and canonical-JSON cases check derived-only results, digest
   lengths, and permanently False dispatch, replay and external outcome
   properties. The fixture does not execute OS commands or a ToolBackend.
   This tests local repr/error minimization, not side-channel resistance.

4. **Planner terminal/independent DAG waves** —
   `tests/test_planner_terminal_independent_run946.py`, commit
   `67c77c1f0adf986f8b9d1ebee46135489cc85796`.
   FAILED, CANCELLED and BLOCKED root outcomes should block their transitive
   descendants and fan-in step, while an unrelated root and its child remain
   runnable through normal revision-guarded transitions. Topology identity
   must remain stable, status digest must advance. No actual tool executes.

**Authored new test cases: 24** (5 + 4 + 12 + 3).
The initial Atomic-only Ruff failure above is recorded explicitly. Additional
latest-HEAD CI was still in progress while this report was prepared; do not
promote earlier-head six-job GREEN to acceptance of these new tests.

## Threat boundary and remaining integration work

- A retained local token does not authenticate the writer, grant consent,
  establish trusted time, or prove other owners' database history was honest.
- A COMMIT-UNKNOWN local row could coexist with a missing, duplicated or
  unknowable external side effect. Never infer safe automatic retry.
- A deterministic mock receipt does not provide backend authorization or
  independently verified provenance, even when its SHA-256 and JSON are
  stable across processes.
- A Planner's in-memory failure propagation is not restart-atomic durable
  orchestration; connect it to an occurrence-scoped audit/authorization
  journal only after exact-HEAD GREEN for lower-level invariants.

## Next priorities

Confirm latest exact-source/test HEAD Windows/Ubuntu × Python 3.11–3.13 CI,
repair only observed failures via normal Contents API, then implement durable
Planner recovery and strict Memory WAL/SHM CAS/expiry isolation with focused
regressions. Keep PR #5 Draft and UI PR #9 untouched/unmerged, protect the V2
evaluation gate, and keep V3 free-only/nonpromoting.
