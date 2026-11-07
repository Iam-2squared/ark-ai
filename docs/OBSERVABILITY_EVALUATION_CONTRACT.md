# ARK Observability and Evaluation Contract

Work basis: `b901099182ffc0bcd897e73904be073c98eabb0f`

This document defines local-first observability for ARK's continuous JARVIS foundations. It does not add external telemetry, cloud logging, paid services, or new evaluation authority.

## Goals

Observability must make failures reproducible without weakening privacy, authorization, or frozen evaluation boundaries.

The baseline answers:

- what component acted;
- what deterministic request/plan/memory identity was involved;
- which contract/schema revision applied;
- what state transition occurred;
- when it occurred according to the component's trusted clock;
- whether the operation succeeded, conflicted, was denied, or remained ambiguous;
- which exact code/evidence identity produced a test result when available.

## Local-first event envelope

Foundation events should share a small typed envelope containing:

- event type and schema version;
- component name/revision;
- deterministic correlation ID;
- trusted timestamp;
- outcome category;
- content-free provenance references;
- optional parent correlation ID.

The envelope does not require raw prompts, Memory plaintext, tool arguments, media, credentials, or secrets.

## Correlation

Correlation identifiers should reuse existing deterministic identities where possible:

- Memory: memory ID + revision;
- actions: ToolCall request ID;
- planner: plan ID + step ID + revision;
- proactive work: trigger identity;
- Personal Context: bundle/provenance digest;
- multimodal observations: observation digest.

A correlation ID is not authorization and cannot be used as a bearer token.

## Outcome taxonomy

At minimum, foundation metrics distinguish:

- success;
- deterministic conflict/CAS loser;
- policy denial;
- integrity rejection;
- schema rejection;
- expiry rejection;
- dependency blocked;
- audit persistence failure;
- backend known failure;
- backend outcome unknown;
- user/hardware/external gate blocked.

This prevents materially different failure modes from being collapsed into one generic error counter.

## Privacy

Observability follows the privacy/data-lifecycle contract.

- no external telemetry by default;
- no raw Personal Context plaintext in metric labels;
- no raw action arguments in metric labels;
- no secrets/tokens in logs;
- no unbounded high-cardinality plaintext dimensions;
- content hashes and deterministic IDs are preferred where they provide sufficient debugging value;
- retention must be explicit for any persisted trace store.

Debug mode may increase local detail only through an explicit local configuration and must not silently upload it.

## Deterministic evaluation records

A foundation evaluation record should bind:

- exact repository HEAD or explicit prototype identity;
- test/evaluation suite revision;
- platform/runtime identity when relevant;
- schema/contract revisions;
- deterministic fixture/input identity;
- result counts;
- start/end trusted timestamps where available.

Prototype validation is labeled as prototype evidence until the matching repository source is saved and tested. A GREEN unrelated HEAD cannot be cited as evidence for unsaved source.

## Concurrency evaluation

Concurrency results record:

- thread vs process model;
- worker count;
- repeated round count;
- exactly-one/at-most-one/all-success invariant;
- raw infrastructure errors separately from expected domain conflicts;
- exact implementation identity.

A single lucky concurrency pass is not sufficient evidence.

## Action observability

Action tracing preserves the ordering boundary:

`authorization decision -> durable consume -> pre-action audit -> backend -> outcome/reconciliation`

A consumed authorization remains consumed even if later events fail. An unknown backend outcome is a distinct terminal/awaiting-reconciliation state and must not be reported as success or ordinary retryable failure.

## Planner observability

Planner traces record step/revision transitions and dependency-blocking outcomes without treating planner state as action authority.

Recovered `RUNNING` WRITE work is reported as ambiguous until reconciled; restart must not convert it to implicit retry.

## Memory and Personal Context observability

Memory events bind lifecycle operation, memory identity, revision, scope identity, and trusted time without duplicating Memory plaintext.

Personal Context traces bind retrieval policy revision and content-free provenance. They may report counts by namespace but should not place private source text into metric names or labels.

## Multimodal/proactive observability

Voice/vision fixture evaluations record observation schema/adapter identities and content digests rather than raw media when not required.

Proactive scheduler metrics distinguish evaluated, suppressed, prepared, surfaced, authorized, executed, and deduplicated states. A prepared or surfaced item is never counted as an executed action.

## CI and frozen evidence

Normal CI may exercise foundation code, mocks, deterministic fixtures, packaging, and compatibility tests.

It must not silently open protected/frozen V2 evaluation data, generate a real Candidate, invoke paid/external compute, or reinterpret a later foundation test as a historical V1/V2/Local UI/Launcher PASS.

## Initial implementation priority

1. define typed local event/result envelopes;
2. instrument Memory conflict/integrity/schema paths;
3. instrument planner transitions and recovery;
4. instrument durable authorization and ActionExecutor ordering;
5. add deterministic concurrency-result helpers for tests;
6. add Personal Context/proactive counters using content-free labels;
7. expose only local UI diagnostics that preserve these privacy constraints.

## Integration rule

This contract is reversible foundation work. It changes no frozen contract/evidence, opens no protected evaluation, authorizes no Candidate generation/promotion, and requires no paid or external service.
