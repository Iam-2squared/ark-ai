# Personal Context Source Implementation Plan

Status: source-ready implementation plan for Draft PR #8. This is not roadmap PASS evidence.

Work basis: `016524336ea5c97975f6de1e9d7dbae00393b1b6`.

## Goal

Build deterministic, privacy-preserving Personal Context on top of the local Memory store without giving context assembly any new action authority.

## Required Memory boundary

Personal Context must not fetch each namespace in a separate database snapshot. A single bundle request must materialize every requested namespace inside one short read transaction so the bundle cannot mix records from before and after a concurrent writer commit.

The Memory API should accept one owner plus an ordered sequence of namespaces and return a fully materialized snapshot for those namespaces. Scope isolation remains exact: data from another owner or namespace is never eligible.

## Deterministic assembly

Context assembly should:

- preserve caller-specified namespace priority;
- rank candidates deterministically inside each namespace;
- apply a per-namespace cap and total bundle cap;
- use round-robin selection across eligible namespaces so one large namespace cannot starve the others;
- reject duplicate memory identities with conflicting payloads;
- keep memory plaintext as data rather than interpreting it as instructions or tool calls;
- produce content-free provenance containing memory identity, namespace, revision, content digest, and selection rank;
- derive a bundle identity only from canonical structured metadata and the selected record identities/revisions/digests.

Equivalent candidate sets must produce the same selected records and bundle identity regardless of mapping or insertion order.

## Failure behavior

Malformed or internally inconsistent persisted Memory rows fail closed before context assembly. If the Memory component is unavailable, only Personal Context should be dependency-blocked; ordinary conversation and unrelated read-only capabilities may remain ready.

No Personal Context failure may authorize a tool call, weaken the PermissionGate, consume a one-shot authorization, or trigger computer control.

## Tests required before integration

Repository tests should cover:

- exact owner and namespace isolation;
- a writer racing a multi-namespace reader, proving one coherent snapshot;
- deterministic selection over at least 100 randomized candidate insertion orders;
- per-namespace and total budgets;
- round-robin fairness;
- duplicate/conflicting identity rejection;
- canonical content-free provenance;
- instruction-like and shell-like plaintext round-tripping strictly as data;
- component-scoped startup degradation when Memory is unavailable.

## Integration order

1. harden Memory initialization, row validation, CAS, expiry cleanup, and coherent multi-namespace snapshot;
2. implement Personal Context selector and bundle contracts;
3. connect startup readiness so only the dependent lane is blocked on Memory failure;
4. expose read-only Personal Context to conversation assembly;
5. keep tool/action execution governed independently by the registry, authorization, audit, and executor chain.

No external compute, paid service, Candidate generation, protected evaluation opening, frozen-contract change, real computer action, or main merge is authorized by this plan.
