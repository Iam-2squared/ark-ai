# JARVIS offline recovery, coherent Memory, and retention custody — Run423

**Status:** Reversible, disconnected fixture implementation and negative tests on
Draft PR #8. **No live JARVIS PASS, authorization, consent, erasure, or dispatch.**
This note reports source semantics and the test matrix; exact-head CI results and
job IDs belong in the canonical `docs/PROJECT_STATUS.md` checkpoint.

## Work basis and boundaries

- Opened at Run422 checkpoint `8e56dac72e2681e06755db477e8bc0898ddff2f2`,
  whose PR-triggered CI #1130 / `40191296165` was six-job SUCCESS.
- Target: `research/jarvis-foundations` / Draft PR #8, separate from
  Draft/unmerged V3 PR #5 and main.
- Source changes do not alter the frozen Memory v1 or ActionAudit v1 schema,
  frozen V1/V2/Local UI/Launcher evidence, V3 Contract 1, protected evaluations,
  or external compute/approval gates.

## Package A — original Planner recovery snapshot and per-step binding

`src/ark/agency/synthetic_write_plan_recovery_review.py` now retains the
**initial** `SyntheticPlanRecovery` and nested `SyntheticPlanTail` field
carriers through every per-step SQLite callback and the final result constructor.
The previously protected per-step returned reviews did not themselves protect
that initial journal snapshot: a reflected mutation of
`baseline.step_statuses` could change the terminal-descendant hold diagnosis
after the journal read without changing the immutable `PlanStep` input.

Each per-step diagnostic must also match the original journal's exact step
identifier, request identity, registry revision and step state before inclusion.
A reused, mismatched or stale per-step receipt is rejected. This **never**
turns a diagnosis into executable authorization. Unknown/reserved PENDING WRITE
and WRITE descendants remain non-replayable without independent real outcome
proof.

`tests/test_plan_recovery_baseline_state_epoch_run423.py`: six initial
snapshot/tail mutations, four per-step subject/status substitutions, one
unchanged RUNNING+PENDING plan fixture (**11 parametrized pytest cases**).
All backends are explicit never-dispatch fakes.

## Package B — coherent Memory snapshot hydrated row identity

`src/ark/memory/coherent_snapshot_review.py` now pins the *actual*
`MemoryRecord.scope` and `MemoryRecord.metadata` objects, as well as the
original ten scalar carriers, while retaining existing value/type/metadata
integrity comparisons. An equal-valued replacement is still a different
hydration epoch. Keeping actual references avoids id-only identity reuse.

The single SQLite read transaction, row count limits, content-free witness
payload, query hash, expiry behavior and frozen Memory v1 SQL schema remain
unchanged. This is local continuity checking, **not** an authenticated data
source, consent ledger, or simultaneous cross-process snapshot.

`tests/test_memory_snapshot_hydrated_identity_run423.py`: eleven injected
equal-valued nested/scalar substitutions, plus one stable content-minimized
two-record snapshot (**12 parametrized pytest cases**). No external data
source or personal-data disclosure.

## Package C — privacy retention recheck result and cached input custody

`src/ark/personal_context_retention_recheck_review.py` retains original
owner/namespace carriers and cached inventory header/item carriers. It now
checks them after the final `SyntheticRetentionRecheck` constructor, rechecks
the current inventory's nested items and digest, and rejects forged queue,
digest, time or revocation fields. The candidate `expired_memory_ids` and
`unbounded_memory_ids` are **human-review diagnostics**, never deletion
requests. Even matched independent Memory/revocation reads are not an atomic
cross-database snapshot or proof of completed erasure.

`tests/test_retention_recheck_result_custody_run423.py`: twelve constructor
mutations of cached, current or returned receipt carriers plus a valid
non-authorizing review queue (**13 parametrized pytest cases**). No actual
personal-data deletion, notification, disclosure, or consent assertion.

## Interactions and remaining gaps

These three modules are intentionally independent and reversible. Each
fixture rejects changes to previously observed local evidence; none supplies
authenticated issuer identity, externally attested clock, real backend outcome,
durable distributed WRITE idempotency, or privacy/legal authorization.

**Required next engineering work:** bounded four-store partial-prefix
recovery with explicit orphan pre-action evidence; CAS and multiprocess
expiry/snapshot invariants; privacy-safe revocation across independent stores;
verified trusted-clock and issuer interfaces; fixture-only Observation and
Scheduler correlation. Never automatically dispatch or replay an uncertain
WRITE and never open protected evaluation, generate Candidate weights,
promote, or merge main without the corresponding explicit gate.

**Free-only invariant:** no paid/external GPU compute, paid API, new account or
credential, potentially billable service, live device/sensor, actual Tool
execution, destructive operation, or frozen-contract modification.
