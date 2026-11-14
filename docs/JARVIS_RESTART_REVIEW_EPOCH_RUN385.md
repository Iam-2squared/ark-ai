# ARK — Run 385: Disconnected restart/source epoch boundaries

This engineering note describes four **FREE-only, reversible** safety packages.
It is not approval to connect a real ToolBackend or personal-data pipeline.
All reviewers and tests use synthetic/local SQLite state. Previous frozen
V1/V2/Local UI/Launcher contracts/evidence and PR #5 gates are unchanged.

## 1. Multi-namespace Memory snapshot source identity

`review_synthetic_memory_scopes` now requires an initialized Path source and
pins **Path object identity** across a single SQLite read transaction.
An equal pathname represented by a later Path object is still rejected.
This matters because reflected in-process retargeting can otherwise present
the same string path after a callback and evade a simple value comparison.

Fixture cases cover stable operation, equal-value replacement under row
hydration (with and without an exact prior snapshot), wrong path type,
and retargeting to a nonexistent source. No new source is created.

The comparison does **not** detect an OS-level replacement at the same inode
or pathname, and no local hash authenticates historical provenance.

## 2. Claim/Occurrence recovery source and ToolCall epoch

`review_synthetic_claim_write_provenance` now pins path identities for the
cancellation journal, Planner journal, ActionAudit, association sidecar, and
optional Occurrence/Audit sidecar from the beginning of the cross-store
read-only review until after the final evidence read. It also pins the
ToolCall input arguments carrier and request identity and rechecks the
ToolRegistry revision without executing the registered backend.

Late equal-path substitutions after the last association read, as well as
a reflected ToolCall scope mutation, must reject. Four SQLite stores still
have no global atomic transaction, and `first == second` is not trusted
consent or proof of a real WRITE effect. A post-review mutation remains
possible, so these receipts never authorize dispatch or automatic retry.

## 3. Personal Context independently retained revocation prefix

`review_synthetic_context_reuse` now requires an exact retained revocation
witness when supplied, validates its integrity before any fresh Memory
projection, pins its immutable scalar/tuple values, and validates both its
integrity and unchanged epoch again after the projection and veto reads.

A reentrant callback that swaps a valid earlier witness for another
locally valid newer prefix must reject. A malformed replacement also
rejects. An unchanged independently retained earlier prefix remains usable
as a **diagnostic veto**, not consent or permission to expose context.
No Memory row or revocation marker is deleted or exported.

## 4. Planner recovery/append witness and path epochs

`SyntheticPlanJournal.recover` pins retained tail scalar fields, requires
the source to remain the **same Path object**, and rechecks retained-shape
and original scalar evidence after replay, before returning a diagnosis.
Previously a reflected replacement with a different locally valid prefix
could be accepted when it matched the replayed in-database history.

`SyntheticPlanJournal.append` also requires the original source identity
through the speculative SQLite writer transaction and constructs the result
**before COMMIT**. A callback changing the source during replay causes a
rollback rather than a misleading successful append to a stale source.

Tests inject a coherent older retained prefix, a bool/int shape spoof,
equal-path substitution, append retarget/rollback, and malformed source;
normal RUNNING recovery continues to be **UNKNOWN / no auto replay**.

## Boundaries

- Scope: local Python object/source epochs and bounded SQLite reads only.
- No issuer or subject authentication, external attestation, trusted clock,
  signed witness custody, global multi-database transaction, filesystem
  inode replacement defense, or real-world exactly-once effect claim.
- No new service, new secrets, live camera/microphone/screen data, paid GPU,
  training/Candidate generation, protected V2 FINAL opening, external WRITE,
  irreversible deletion, automatic promotion, or main merge.
- The new tests and CI are evidence only for their exact commit SHA when
  those jobs finish successfully. No GREEN status is implied by this note.

## Follow-up

Prioritize exact-head multi-platform CI, then extend source-epoch/restart
invariants on the Planner/Occurrence/ActionAudit boundary and memory privacy
retained-witness boundaries. A future authenticated approval and clock design
requires explicit architecture/privacy review; it is **not** implicitly
selected or activated by these synthetic checks.
