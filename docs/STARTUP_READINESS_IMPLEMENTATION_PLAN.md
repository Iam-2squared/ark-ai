# Startup Readiness Implementation Plan

Status: source-ready reversible plan for Draft PR #8.

## Deterministic component model

Each startup component declares:

- stable component ID;
- explicit dependency IDs;
- local readiness state;
- optional stable failure code.

Initial effective states are `READY`, `DEGRADED`, or `BLOCKED`. `DEPENDENCY_BLOCKED` is derived only by propagation.

Duplicate component IDs, unknown dependencies, self-dependencies, cycles, duplicate dependency IDs, blank failure codes, and raw unknown states fail closed.

## Canonical graph

Registration order is not semantic.

Construction snapshots all component specs, then canonicalizes by component ID. Dependency edges are canonicalized for identity calculation. Topological evaluation uses deterministic tie-breaking by component ID.

The graph is immutable after construction.

## Propagation

For each component in deterministic topological order:

1. if its local state is `BLOCKED`, effective state is `BLOCKED`;
2. otherwise, if any required dependency is `BLOCKED` or `DEPENDENCY_BLOCKED`, effective state is `DEPENDENCY_BLOCKED`;
3. otherwise, effective state is its own local state.

A component that is `DEGRADED` never grants a capability that its local probe did not prove. Dependency edges remain explicit; unrelated lanes are not globally disabled.

Examples:

- Memory failure blocks Personal Context, not local text conversation;
- Action Audit failure blocks write-capable execution, not unrelated read-only work;
- planner recovery failure blocks persisted-task resume, not a new conversation;
- vision-adapter failure blocks only consumers that declare vision as required.

## Snapshot identity

Each startup epoch produces an immutable readiness snapshot whose digest binds:

- schema version;
- canonical component IDs;
- canonical dependency edges;
- local states;
- effective states;
- stable failure codes.

Timestamps and registration order are excluded from the deterministic identity. A new explicit revalidation creates a new startup epoch/snapshot.

## Diagnostics

Diagnostics expose only component IDs, effective states, stable failure codes, schema revisions, counts, and non-secret hashes. Private Memory content, raw action arguments, credentials, and media payloads are excluded.

## Required tests

- 200+ randomized registration orders -> one readiness digest;
- duplicate/unknown/self/cycle dependency rejection;
- graph and snapshot immutability;
- Memory BLOCKED -> Personal Context DEPENDENCY_BLOCKED while conversation remains READY;
- Action Audit BLOCKED -> write executor DEPENDENCY_BLOCKED while read lane remains available;
- planner recovery BLOCKED -> task-resume lane blocked only;
- repeated evaluation of unchanged local state -> identical digest;
- explicit revalidation after a local-state change -> new snapshot identity.

## Integration order

Implement after the local stores expose reliable open/validate/recovery results. Startup readiness consumes those results; it does not repair a malformed store or weaken its component-specific integrity policy.

This plan changes no frozen evidence, V3 Contract, protected evaluation gate, Candidate state, or main-merge authority.
