# Run400 — Snapshot, planner topology, cached readiness and context callback custody

**Scope:** local-first, disconnected, synthetic safety foundations on Draft PR #8.
**Starting exact HEAD:** `d1fcc162192cf2473c35aff9ade9fed89aa83727` (the
Run399 checkpoint; its own #833 / `40118475332` completed 6/6 GREEN).
**Integration:** no merge or live action authority; V3 PR #5 remains under its own
Draft/NOT_PASSED review gate. All changes use ordinary GitHub Contents writes.

## Threat model and explicit failure boundaries

The reviewed dataclasses are frozen only through normal Python assignment.
Caller-controlled validation callbacks and test reflection can still replace
carriers or mutate a nested object. For an offline diagnostic, a value-equal
replacement is *not* evidence that the originally captured source remained
stable throughout the review. The tests below exercise **observed** changes
at precise callback boundaries, not malicious arbitrary-code execution.

| Independent path | Original unchecked boundary | New fail-closed review |
| --- | --- | --- |
| Memory coherent snapshots | A `CoherentSnapshotRequest.namespaces` tuple could be replaced by an equal-valued tuple during text tokenization, row hydration or metadata hashing; tuple equality alone accepted its later epoch. | Keep original namespace tuple **object** and recheck its identity together with the typed request fields during every existing snapshot phase. |
| Planner/Claim/Occurrence recovery | The outer `SyntheticPlanJournal._steps` tuple stayed identical while a nested `PlanStep` or its ToolCall/dependency carrier changed inside Registry or graph callbacks. | Pin individual original PlanStep, step name, action object/request digest, arguments carrier and dependency tuple **before** registry bind; recheck after bind, PlanGraph construction and other existing cross-store read boundaries. |
| Startup readiness | `StartupSnapshot.state()` and `root_blockers()` checked graph integrity, then called the reentrant caller identifier validator; reflected mutation during that validator could change returned READY/blocker data after the check. | Revalidate cached snapshot integrity **after** caller identifier validation and before computing either returned diagnosis. |
| Personal Context | Per-item provenance `_hash` callbacks ran before a final source/selection epoch review. A temporary privacy scope, Memory field or selection-policy alteration could be restored by a later item hash. | Move the existing full source-epoch predicate ahead of the selection loop and enforce it before/after **each** provenance hash and after each constructed item. |

## Exact regression fixtures

- `tests/test_memory_snapshot_namespace_carrier_run400.py`: one stable
  deterministic local snapshot and three equal-value namespace tuple swaps at
  query, row and metadata callback boundaries (**4 cases**).
- `tests/test_recovery_nested_topology_epoch_run400.py`: inert baseline;
  first-bind mutation of step ID, equal-value ToolCall replacement,
  equal-value dependency carrier replacement and equal-value arguments mapping;
  graph-constructor dependency rebasing (**6 cases**).
- `tests/test_startup_snapshot_getter_recheck_run400.py`: stable BLOCKED /
  DEPENDENCY_BLOCKED diagnosis; callback-caused forged READY and removed root
  blocker between cached integrity check and use (**3 cases**).
- `tests/test_personal_context_selection_callback_epoch_run400.py`: stable
  two-row local selection; first provenance hash temporarily mutates original
  Memory content, namespace scope or round-robin budget and must fail *before*
  the second item's hash could restore input (**4 cases**).

**Total introduced: 17 focused synthetic cases** in four source/test packages.
No preexisting passing test is intentionally weakened, no Memory v1 SQL DDL or
frozen interface contract changes, and no active ToolBackend is instantiated.

## Honest non-proofs and integration blockers

- A coherent SQLite read snapshot covers **one** SQLite connection, not an
  atomic snapshot across Memory, revocation, planner, reservation and audit
  databases. A final check cannot prevent races **after** return.
- Object identity and a local SHA are not cryptographically authenticated
  history, human issuer/consent, operating-system file descriptor custody,
  globally monotonic/trusted time, or authenticated external action receipts.
- Inert preparedness, mock audit and reservation rows do not prove a real
  WRITE happened; RUNNING/UNKNOWN must never authorize an automatic retry.
- Neither this review nor its tests run a model, use paid/external compute,
  create real media captures/notifications, erase private data, supply new
  credentials, approve an adapter, open protected V2 FINAL, or promote a
  Candidate. The user-gated main merge remains untouched.

## Dependency-aware Next plan / 今後の方針

1. Observe exact-source/test SHA GitHub Actions runs and confirm all six jobs
   per tested HEAD; repair genuine failures only through the normal file
   Contents path. Do not inherit GREEN from a predecessor or duplicate runs.
2. Extend local crash/restart reconciliation across PlanJournal, Claim,
   Occurrence, Audit and an **inert** mock executor; keep UNKNOWN non-replayable.
3. Review Memory CAS/expiry and privacy revocation inventory against
   independently persisted witnesses, without frozen DDL changes or erasure.
4. Plan explicit trusted-clock and authenticated approval-provenance **ports**
   without issuing credentials, connecting paid services, or enabling actions.
5. Continue isolated Observation/Scheduler and V3 free-only
   approval/path/identity/reproducibility guards; preserve all protected gates.
