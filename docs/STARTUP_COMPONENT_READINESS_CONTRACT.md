# Startup Component Readiness Contract

Status: reversible local-first foundation contract.

## Purpose

ARK startup must determine availability per component instead of reducing the whole system to one global ready/error flag.

Each component reports one of:

- READY
- DEGRADED
- BLOCKED
- DEPENDENCY_BLOCKED

A component may be marked READY only after its own local state has passed schema/version checks and any required recovery step.

## Dependency graph

Startup uses an immutable acyclic dependency graph with:

- unique component IDs;
- no unknown dependency IDs;
- no self-dependencies;
- no cycles;
- deterministic evaluation independent of registration order.

The readiness snapshot is canonicalized from component IDs, dependency edges, local states, and stable failure codes so repeated evaluation of the same state produces the same identity.

## Lane-scoped failure behavior

A failure blocks only the affected component and strict dependents.

Minimum relationships:

- Memory -> Personal Context
- Memory -> context-dependent proactive features
- Planner recovery -> persistent task resume
- Tool Registry -> tool execution
- Action Audit -> write-capable execution
- durable authorization -> write-capable execution
- observation adapter -> consumers that require that modality

Core local conversation does not automatically depend on Memory, Action Audit, or write-capable execution.

Examples:

- Memory BLOCKED: Personal Context is DEPENDENCY_BLOCKED; text conversation may continue without remembered context.
- Action Audit BLOCKED: write-capable execution is DEPENDENCY_BLOCKED; unrelated read-only work may continue.
- Planner recovery BLOCKED: persisted-task resume is unavailable; a new unrelated conversation may still start.
- Vision adapter BLOCKED: vision is unavailable; text/voice lanes need not fail if independently ready.

DEGRADED mode may remove capability but may never add capability.

## Startup sequence

1. load static local configuration;
2. validate the component dependency graph;
3. open independent local stores;
4. run explicit initialization/migration where required;
5. validate current schema and persisted integrity;
6. recover journals/anchors where applicable;
7. compute local component states;
8. propagate dependency blocking deterministically;
9. freeze a readiness snapshot for the startup epoch;
10. expose only lanes whose required dependencies are available.

A blocked component must not silently become READY because a later request happens to work. Re-entry requires explicit revalidation.

## Diagnostics

Readiness diagnostics should be content-minimized. They may include component ID, schema version, stable failure code, counts, and non-secret hashes. They should not duplicate private Memory content or raw request payloads.

## Validation requirements

Repository implementation should test:

- registration-order randomization yielding the same readiness identity;
- duplicate component rejection;
- unknown dependency rejection;
- self-dependency rejection;
- cycle rejection;
- Memory failure blocking Personal Context but not unrelated conversation;
- Action Audit failure blocking write-capable execution;
- planner recovery failure blocking task resume only;
- deterministic readiness snapshots across repeated runs.

## Boundaries unchanged

This contract does not change frozen V1/V2/Local UI/Launcher evidence, V3 Contract semantics, Candidate state, protected evaluation gates, or main-merge authority.
