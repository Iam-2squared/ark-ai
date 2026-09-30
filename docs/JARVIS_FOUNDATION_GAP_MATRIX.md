# ARK JARVIS Foundation Gap Matrix

Work basis: `6e0539078a6dd0005003a6733050e3faf0c8e6c0`

This matrix records the current repository implementation against the already-defined JARVIS foundation contracts. It is a development queue, not a roadmap PASS record.

| Area | Current repository state | Verified gap | Safe next implementation |
| --- | --- | --- | --- |
| Planner topology | DAG validation, revision-guarded transitions, immutable `steps` mapping, immutable status snapshots, and sorted traversal exist for exact `PlanStep` inputs | `PlanGraph` does not reject non-`PlanStep` duck-typed objects, so externally mutable topology can enter the graph; focused immutability coverage is also not yet saved | require exact `PlanStep` ingress, then land topology/status immutability regressions |
| Planner transition types | exact `StepState` and exact non-bool non-negative integer revision checks exist | focused regression coverage for raw-string state, bool revision, and negative revision is not yet saved | land focused tests |
| Planner transition table | transition rules use immutable mapping + `frozenset`; FAILED blocks pending descendants | explicit CANCELLED/BLOCKED terminal transitions do not propagate dependency blocking, leaving descendants permanently PENDING with no ready path | propagate all non-success terminal dependency states to pending descendants and add regressions |
| Plan input determinism | `PlanStep.depends_on` requires an ordered `Sequence` and normalizes it to tuple; ready/descendant traversal is sorted | focused unordered-container and input-order regression coverage is not yet saved | land focused tests |
| Memory identity | deterministic scope/source identity exists | persisted identity is not recomputed on every read/mutation; same deterministic ID can mask persisted scope/source corruption | validate stored owner/namespace/source -> memory_id before surfacing or mutating |
| Memory content integrity | content SHA-256 is persisted | persisted content digest is not recomputed on read/update/delete | fail closed on digest mismatch before read or mutation |
| Memory metadata | write metadata is constrained/canonicalized | persisted JSON storage class and canonical byte representation are not verified before parsing | require TEXT storage, canonical JSON representation, and contract limits before surfacing |
| Memory record storage classes | SQLite column affinity exists | REAL timestamps/revisions and BLOB metadata can be silently converted by Python readers | validate exact SQLite storage classes before any `int()`/JSON conversion |
| Memory event integrity | event rows are persisted and scope-filtered | event reader currently converts persisted revision/timestamp with `int()` and does not validate canonical memory ID, scope text, operation domain, or non-negative time | validate exact event-row storage classes and domains before constructing `MemoryEvent` |
| Memory time integrity | timestamps are persisted | writer samples clock before acquiring a write lock; update/delete do not reject trusted-clock rollback below stored history | acquire write lock first, validate persisted row/history, then sample trusted clock and enforce monotonicity |
| Memory initialization | schema version guard exists | concurrent first-open can race schema creation; ordinary connection open mutates persistent journal mode; negative `user_version` is not explicitly rejected | serialized bootstrap under write transaction, stable connection setup, explicit version domain check |
| Memory schema trust | schema fixture and semantic hardening plan exist | runtime does not yet prove same-version managed table/index/trigger SQL, including non-index collation and AUTOINCREMENT semantics | exact managed-schema validation before use |
| Memory CAS | revision predicate exists on update/delete | create race can surface raw SQLite integrity errors and read-before-write windows are broader than necessary | serialize writer path and translate expected contention into `MemoryConflictError` |
| Memory expiry | expiry filtering and physical purge exist | purge deletes by memory ID only, so a concurrently refreshed row can be stale-deleted | bind delete to observed revision + expiry predicate and count actual deletions only |
| Action audit | SQLite audit excludes raw ToolCall arguments | bootstrap/schema/storage validation is incomplete; clock is sampled before writer lock; negative schema version is not explicitly rejected; arbitrary caller-provided `outcome` text can persist sensitive plaintext | serialized bootstrap + exact schema/row validation + lock-before-clock monotonic append; constrain new-write outcomes to a bounded content-free domain while preserving required legacy-read compatibility |
| Tool registry | ToolSpec/ToolBackend contracts, deterministic fixtures, and registry-binding semantics exist | immutable runtime registry and bound-action implementation/tests are not yet landed | immutable duplicate-rejecting registry, deterministic revision, exact capability binding |
| Permission policy | exact capability/scope and in-memory one-shot checks exist for normal typed inputs | one-shot consumption is process-local/restart-replayable, and the public gate does not exact-type-check `ToolSpec`/`ToolCall`/grant/token inputs before effect branching, allowing type-confused duck-typed values to weaken WRITE handling | exact-type fail-closed ingress + non-consuming grant validation split, then local SQLite durable one-shot ledger storing token digest only |
| Action time | policy receives caller-supplied `now_ms` | execution boundary does not yet own trusted time | trusted-clock ActionExecutor owns authorization/audit time |
| Audit-before-action | audit and policy exist independently | no executor forces durable authorization consumption -> pre-action audit -> backend ordering | mock/disconnected ActionExecutor with fail-closed audit sequencing |
| Action replay | request IDs are deterministic and bound-action vectors are frozen | durable occurrence state is not yet implemented against exact registry-bound identity | derive occurrence identity from bound_action_id + one-shot digest; retain request_id only as grouping identity; no blind retry for ambiguous writes |
| Planner recovery | recovery contract is documented | no repository planner journal implementation yet | append-only local journal bound to canonical topology and revision replay |
| Personal Context | Memory store provides scope-isolated retrieval | no coherent multi-namespace snapshot API or context-bundle/fairness/provenance layer exists in repository source | one-transaction multi-namespace snapshot, then deterministic retrieval with content-free provenance |
| Proactive scheduler | proactive contract exists | no scheduler state implementation exists | local SQLite trigger state with deterministic identity, CAS, cooldown, deduplication |
| Voice/Vision | typed content-minimized ObservationEnvelope source and deterministic fixture exist | matching repository tests and fixture adapters are not yet landed; live capture remains intentionally disconnected | land envelope tests, then fixture-only text/transcript/image/screen adapters; no hardware/cloud dependency |
| Computer actions | safety contract exists | real adapters correctly remain disconnected | keep disconnected until registry + durable auth + audit + executor are integrated GREEN |
| V3 independent guards | PR #5 contains extensive pre-paid-compute tooling; free review identified runtime/preflight approval binding gaps | reviewed preflight artifact is not yet runtime-consumed and full training lacks a distinct durable post-preflight approval artifact | close only free guard plumbing; do not start external compute or protected evaluation |

## Dependency queue

The highest-leverage source order remains:

1. harden Planner exact `PlanStep` ingress and non-success terminal descendant propagation, then land focused invariant tests;
2. Memory initialization/schema/row/event integrity, CAS, trusted clock, and expiry hardening;
3. Action Audit initialization/schema/row/timestamp hardening;
4. immutable ToolRegistry;
5. exact-type PermissionGate ingress + non-consuming grant validation split;
6. durable registry-bound one-shot authorization ledger and execution occurrence;
7. trusted-clock audit-before-action ActionExecutor over mocks;
8. planner persistence/recovery;
9. Personal Context retrieval;
10. proactive scheduler;
11. fixture-only multimodal adapters and local UI integration.

Items 1-3 can proceed independently. Items 4-6 form one execution-safety chain. Personal Context depends on hardened Memory. Real computer actions depend on the entire execution-safety chain and remain disconnected.

## Current validation evidence not yet landed as source

Isolated prototype work has already exercised:

- planner focused invariants for exact typed source plus newly isolated ingress/terminal-propagation edge cases;
- SQLite bootstrap with `busy_timeout + BEGIN IMMEDIATE` and no ordinary-open journal-mode mutation;
- thread and multi-process first-open/CAS behavior;
- exact persisted-row storage-class and deterministic-identity checks;
- event-row fail-closed validation requirements;
- expiry refresh race protection using revision-bound conditional delete;
- Action Audit lock-before-clock monotonic append with legacy-history preservation;
- immutable ToolRegistry identity/reference-vector reproduction;
- restart-safe registry-bound exactly-once one-shot consumption;
- planner hash-chain recovery;
- owner/namespace-isolated Personal Context;
- proactive trigger deduplication/cooldown.

Prototype evidence is not repository implementation evidence. Each item becomes repository evidence only after the corresponding source/tests are saved and exact-head CI is GREEN.

## Boundaries unchanged

No item in this matrix authorizes paid/external compute, real Candidate generation, protected/frozen V2 evaluation opening, Candidate promotion, frozen-contract changes, destructive/irreversible operations, new credentials/account connections, physical hardware actions unavailable through authorized tools, or main merge.
