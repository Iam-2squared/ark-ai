# JARVIS synthetic source/topology review epochs — Run 386

Status: **research fixture only; NOT_PASSED for live execution**. This document
describes additive safety work in Draft PR #8. It does not modify frozen
contracts, Memory v1 DDL, V1/V2 evaluations, Local UI or Launcher.

## Threat model and concrete changes

The modeled adversary is reentrant in-process mutation of a research fixture
between two otherwise valid checks (including reflected mutation of frozen
dataclasses and rebinding a `Path` to a value-equal, different object). It is
not a proof against compromised OS, hostile same-path file replacement,
untrusted Python interpreter, forged timestamps or colluding SQLite stores.

1. **Synthetic occurrence reservation**
   (`src/ark/agency/durable_occurrence_review.py`):
   capture the initialized source before caller-controlled registry binding;
   pin the connection URI to that captured Path; reject changed source identity
   before opening the writer and again within the transaction and before
   COMMIT. Reentrant swaps of a destination to another/equal Path refuse the
   synthetic reservation without creating an alternative ledger. Read-only
   counts now have their own source epoch. A committed fixture marker is **not**
   human approval, proof of an external effect or permission to dispatch.
2. **Planner journal topology**
   (`src/ark/agency/planner_journal_review.py`):
   bind the input step tuple identity and canonical PlanGraph topology before
   replay/append, and re-evaluate both before committing. A later step tuple
   substitution or nested ToolCall change aborts review; speculative SQLite
   appends roll back. RUNNING remains UNKNOWN, never automatically retried.
3. **Memory ordinary reads**
   (`src/ark/memory/sqlite_store.py`):
   `get` and `events` pin the caller's owner/namespace and the SQLite source
   throughout the read, including **zero-row paths**, where old code could
   bypass some post-read checks. Event queries bind SQL to the original scope,
   not a reflected replacement. This is scope isolation, not consent to use,
   disclosure or deletion.
4. **Proactive synthetic ledger**
   (`src/ark/proactive_synthetic_review.py`):
   count reads pin the source Path and reject changed identity; fixture
   initialization also checks its source before committing schema state.
   Stable fixtures retain content-free deduplication only, with
   `notification_authorized=False` and `dispatch_authorized=False`.

## Regression coverage

New deterministic fixture tests:

- `tests/test_synthetic_occurrence_source_epoch_run386.py`: 7 test
  cases covering early/late/inside-transaction source changes, rollback,
  malformed source and stable inert reservation.
- `tests/test_planner_topology_epoch_run386.py`: 6 test cases covering
  equal-value tuple substitution, nested action mutation, invalid topology
  and unchanged restart-UNKNOWN semantics.
- `tests/test_memory_read_epoch_run386.py`: 10 test cases covering
  empty/populated `get` and `events`, scope/path reentrancy and stable
  private reads.
- `tests/test_proactive_count_source_epoch_run386.py`: 5 test cases
  covering equal/different Path substitution, malformed source and stable
  content-free proactive count.

**Total: 28 added regression cases**. CI verdict belongs to the exact
source/test HEAD tested in GitHub, not to this document's HEAD or a subsequent
checkpoint. Green checks on prior commits cannot be transferred to new code.

## Explicit non-authority boundaries

No external services, purchased services, GPU, model weights, Candidate,
protected V2 FINAL opening, live observations, sensors, notifications, Tool
Backend calls, personal-data exports, main merge or destructive operations.
Each synthetic path either returns a diagnostic/fixture receipt or refuses
it. Scope and Path checks do not provide an atomic multi-database snapshot;
the caller may mutate a source **after** a review returns. SHA/digest matching
without independent custody is not authentic historical evidence. Python
object identity does not establish filesystem identity or a trusted issuer.
No trusted clock, authenticated user consent, external exactly-once effect or
UNKNOWN WRITE automatic retry is established by these changes.

## Next evidence gates

Obtain exact-head Ruff/pytest and Ubuntu/Windows Python 3.11–3.13 CI results.
After that, continue immutable PermissionGate/Registry-bound issuer checks,
Planner recovery/Occurrence/ActionAudit evidence, Memory CAS and retained
witnesses, and privacy-safe Context/Observation/Scheduler fixtures on
independent reversible lanes. Keep PR #5 Draft and NOT_PASSED, with its
protected evaluation closed.
