# Run1450 — Planner and ActionAudit native-COMMIT hard-exit evidence

**Exact parent basis:** Draft PR #8, branch \`research/jarvis-foundations\`, HEAD
\`1cf7b725fcf3c32ff5ffd59bda04ef03d140324b\`. This child branch is based on that
exact parent and targets only PR #8.

## New test-only coverage

1. **Production PlannerJournal RUNNING transition.** A spawned process exits
   immediately after native SQLite COMMIT returns, before connection cleanup
   or the transition receipt. Cold recovery must retain one PENDING → RUNNING
   event, report the step as ambiguous, keep dependent and independent steps
   PENDING, deny dispatch and automatic replay, and reject a stale genesis
   transition attempt. Synthetic ToolCall arguments must not appear in the
   database or sidecars.

2. **Production SQLiteActionAudit append.** A spawned process exits immediately
   after native SQLite COMMIT returns, before connection close or the audit
   receipt. Cold readback must retain exactly two ordered rows (the original
   row and the committed append), validate schema/quick_check and preserve
   content-minimized argument digests without persisting raw ToolCall
   arguments. No executor or backend is invoked.

## Evidence limits

These are disposable local SQLite process-exit regressions. They do not prove
fsync/power-loss durability, independent storage custody, trusted time,
authenticated approval/consent, cross-store atomicity, real backend execution,
or exactly-once external effects. A recovered RUNNING Planner step remains
ambiguous and is never automatically replayed. An ActionAudit row is not proof
that an external action occurred.

No production source, SQLite schema/DDL, public API, frozen contract, V2
evaluation, Candidate, UI/frontend, or main branch is changed. No paid/external
compute, credentials, hardware, destructive operation, training, preflight,
GPU query, or protected evaluation is used. Exact-head CI is required before
any integration or PASS claim.
