# ARK JARVIS Foundation Gap Matrix

Work basis: `c005f4a4fdb88b1d1d9f652eac286e2ad845b568`

This matrix records the current repository implementation against the already-defined JARVIS foundation contracts. It is a development queue, not a roadmap PASS record.

| Area | Current repository state | Verified gap | Safe next implementation |
| --- | --- | --- | --- |
| Planner topology | DAG validation and revision-guarded transitions exist | `PlanGraph.steps` is a mutable public dict after DAG validation | expose immutable topology view and keep mutation internal |
| Planner transition types | `StepState` is typed at API boundary | `StrEnum` equality allows raw strings through membership checks; bool compares equal to integer revisions | exact-type state validation and exact non-bool non-negative revision validation |
| Planner transition table | transition rules are module-level sets | rule sets remain mutable in-process | immutable mapping/frozenset transition table |
| Plan input determinism | `PlanStep.depends_on` is normalized to tuple | unordered iterables such as set can still produce process-dependent dependency order | reject unordered dependency containers or require ordered sequence input |
| Memory identity | deterministic scope/source identity exists | persisted identity is not recomputed when a row is read | validate persisted owner/namespace/source -> memory_id before surfacing |
| Memory content integrity | content SHA-256 is persisted | persisted content digest is not recomputed on read/update/delete | fail closed on digest mismatch before read or mutation |
| Memory metadata | write metadata is constrained/canonicalized | raw persisted JSON is only shape-checked after parse, not checked for canonical representation | validate canonical stored form and contract limits |
| Memory time integrity | timestamps are persisted | update path does not reject trusted-clock rollback below stored update time | enforce monotonic mutation time |
| Memory initialization | schema version guard exists | concurrent first-open can race schema creation; connection open changes persistent journal mode | serialize initialization in one write transaction and remove journal-mode mutation from ordinary opens |
| Memory schema trust | future schema versions fail closed | supported version does not prove required table/index shape | validate same-version schema shape without silently changing v1 DDL |
| Memory CAS | revision predicate exists on update/delete | create race can surface raw SQLite conflict; read-before-write window remains broader than necessary | serialize writer path and translate expected contention into MemoryConflictError |
| Memory expiry | expiry filtering and physical purge exist | stale cleanup can delete a concurrently refreshed row | bind delete to observed revision and expiry predicate; count only actual deletions |
| Action audit | content-free SQLite audit exists | same first-open/journal-mode concurrency risks as Memory; same-version shape not validated | serialized initialization, stable connection setup, shape validation |
| Tool registry | ToolSpec/ToolBackend contracts and deterministic fixture exist | no immutable runtime registry or registry-bound action identity ties durable authorization/recovery to effect/backend revision | immutable duplicate-rejecting registry, deterministic revision, and registry-bound action identity |
| Permission policy | exact capability/scope and in-memory one-shot checks exist | one-shot consumption is process-local and restart-replayable | local SQLite durable one-shot ledger storing token digest only |
| Action time | policy receives caller-supplied `now_ms` | execution boundary does not yet own trusted time | trusted-clock ActionExecutor owns authorization/audit time |
| Audit-before-action | audit and policy exist independently | no executor forces durable authorization consumption -> pre-action audit -> backend ordering | mock/disconnected ActionExecutor with fail-closed audit sequencing |
| Action replay | request IDs are deterministic and bound-action vectors are frozen | the older occurrence contract derives execution identity from request + token only, while the newer registry contract requires exact registry/effect/backend binding | derive occurrence identity from bound_action_id + one-shot digest; retain request_id only as grouping identity; no blind retry for ambiguous writes |
| Planner recovery | recovery contract is documented | no repository planner journal implementation yet | append-only local journal bound to canonical topology and revision replay |
| Personal Context | Memory store provides scope-isolated retrieval | no coherent multi-namespace snapshot API or context-bundle/fairness/provenance layer exists in repository source | one-transaction multi-namespace snapshot, then deterministic retrieval with content-free provenance |
| Proactive scheduler | proactive contract exists | no scheduler state implementation exists | local SQLite trigger state with deterministic identity, CAS, cooldown, deduplication |
| Voice/Vision | typed content-minimized ObservationEnvelope source and deterministic fixture now exist | matching repository tests and fixture adapters are not yet landed; live capture remains intentionally disconnected | land envelope tests, then fixture-only text/transcript/image/screen adapters; no hardware/cloud dependency |
| Computer actions | safety contract exists | real adapters correctly remain disconnected | keep disconnected until registry + durable auth + audit + executor are integrated GREEN |
| V3 independent guards | PR #5 contains extensive pre-paid-compute tooling | real training/evaluation gates remain intentionally unresolved | continue free identity/path/resource/reproducibility validation only |

## Dependency queue

The highest-leverage source order remains:

1. planner invariant hardening;
2. Memory initialization/integrity/CAS/expiry hardening;
3. Action Audit initialization/schema hardening;
4. immutable ToolRegistry;
5. durable one-shot authorization ledger;
6. trusted-clock audit-before-action ActionExecutor over mocks;
7. planner persistence/recovery;
8. Personal Context retrieval;
9. proactive scheduler;
10. fixture-only multimodal adapters and local UI integration.

Items 1-3 can proceed independently. Items 4-6 form one execution-safety chain. Personal Context depends on hardened Memory. Real computer actions depend on the entire execution-safety chain and remain disconnected.

## Current validation evidence not yet landed as source

Isolated prototype work has already exercised:

- immutable planner topology/status and exact transition input checks;
- SQLite bootstrap with `busy_timeout + BEGIN IMMEDIATE` and no ordinary-open journal-mode mutation;
- thread and multi-process first-open/CAS behavior;
- expiry refresh race protection using revision-bound conditional delete;
- restart-safe exactly-once one-shot consumption;
- trusted-clock audit-before-action sequencing;
- planner hash-chain recovery;
- owner/namespace-isolated Personal Context;
- proactive trigger deduplication/cooldown.

Prototype evidence is not repository implementation evidence. Each item becomes repository evidence only after the corresponding source/tests are saved and exact-head CI is GREEN.

## Boundaries unchanged

No item in this matrix authorizes paid/external compute, real Candidate generation, protected/frozen V2 evaluation opening, Candidate promotion, frozen-contract changes, destructive/irreversible operations, new credentials/account connections, physical hardware actions unavailable through authorized tools, or main merge.
