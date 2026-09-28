# Foundation Prototype Evidence — 2026-09-28

Work basis: PR #8 HEAD 955d161c62730412928a05f079eb2dbe8c4e306d.

This file records isolated local validation performed against the current foundation contracts. These results are prototype evidence only until matching repository source/tests land and exact-head CI passes.

## Planner hardening

Validated behaviors:

- read-only planner topology;
- read-only status snapshots;
- immutable transition rules;
- exact StepState transition input;
- exact non-bool non-negative revision input;
- deterministic ready-step ordering;
- stale-revision rejection;
- transitive descendant blocking after failure.

Isolated pytest result: 4 passed.

## Memory read-time expiry ordering

A controlled SQLite race reproduced the current ordering hazard where trusted time is sampled before the database snapshot. A record committed after the early clock sample but already expired by the later read can be returned.

Observed prototype result:

- old ordering: expired record surfaced;
- snapshot-first then clock ordering: expired record hidden.

Required read order:

1. materialize database snapshot;
2. validate rows;
3. sample trusted time;
4. filter expiry;
5. rank and return.

## Local state migration

Prototype used bounded busy timeout, BEGIN IMMEDIATE before schema inspection, explicit DDL/DML statements, source/target validation, in-transaction schema-version update, and reopen verification.

Results:

- 16 concurrent migration callers across 20 rounds: 20/20 PASS;
- injected exception rollback at five migration stages: 25/25 PASS;
- forced process termination at the same five stages: 20/20 PASS;
- interrupted databases always reopened as valid old schema and then migrated successfully;
- unsupported newer schema remained untouched and was rejected.

## Proactive scheduler state

Local SQLite scheduler prototype validated:

- deterministic scope-bound trigger identity;
- cooldown persistence across restart;
- rolling notification-window enforcement;
- 20 concurrent evaluations across 20 rounds with exactly one surfaced notification per trigger identity.

Results:

- identity checks PASS;
- cooldown/window/restart checks PASS;
- concurrency: 20 rounds x 20 callers, exactly-one notification each round.

## Typed observation envelope

Fixture-only observation prototype validated:

- deterministic identity over schema, typed kind, source, trusted ingest time, content digest, adapter identity, privacy scope, and optional parent digest;
- identity changes when any bound field changes;
- raw-string kinds rejected;
- bool/negative timestamps rejected;
- malformed content/parent digests rejected;
- blank source/adapter/privacy fields rejected;
- derived transcript-to-parent digest lineage;
- content-minimized provenance without raw media payload.

Results:

- identity binding PASS;
- 9/9 negative validation cases PASS;
- derived lineage/content minimization PASS.


## Planner input reproducibility follow-up

A process-level hash-randomization check confirmed that allowing an unordered dependency container makes dependency order non-reproducible across interpreter processes. The same four dependency names produced 9 distinct tuple orders across 12 fixed `PYTHONHASHSEED` values.

A source-ready hardening prototype therefore requires an ordered sequence for `PlanStep.depends_on` and rejects sets/frozensets. It also revalidated immutable topology/status views, exact typed `StepState` input, exact non-bool non-negative revisions, and transitive blocking.

Prototype result: immutable views 2/2 PASS; invalid raw states 3/3 rejected; invalid revisions 3/3 rejected; unordered dependency input rejected; transitive blocking PASS.

## Local observability occurrence envelope

A fixture-only local event prototype now binds action telemetry to both canonical request identity and execution-occurrence identity. This avoids collapsing two separately authorized identical actions into one telemetry identity.

Validated properties:

- same canonical request + same execution occurrence -> deterministic event identity;
- same canonical request + different execution occurrence -> different event identity;
- provenance digest order canonicalized across 100 randomized permutations -> identical event identity;
- bool timestamp/schema values rejected;
- raw-string outcome rejected when a typed outcome enum is required;
- execution identity without request identity rejected;
- malformed provenance digest rejected;
- no raw action arguments or bearer-token plaintext are required in the envelope.

Prototype result: 100/100 provenance-order permutations deterministic; 5/5 negative validation cases rejected; distinct execution-occurrence identity separation PASS.

## Repository and boundary status

No model training, Candidate generation, external GPU work, protected evaluation opening, promotion, main merge, or frozen-contract change occurred.

The next repository implementation order remains planner hardening, Memory durability/read ordering, Action Audit durability, reusable local-state migrations/startup recovery, then scheduler/observation source integration behind existing foundation contracts.
