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


## Planner exact-boundary follow-up

A source-ready planner reference implementation was exercised against the current contract boundary with:

- ordered-sequence-only dependencies;
- immutable topology and status snapshots;
- immutable transition-rule sets;
- exact `StepState` transition input;
- exact non-bool non-negative revision input;
- sorted deterministic traversal for ready-step and descendant-blocking logic.

Results:

- 9/9 focused boundary/invariant checks PASS;
- 200 randomized plan registration orders produced one identical failed-root descendant-state digest;
- unordered set dependencies were rejected before topology construction.

This remains prototype evidence because the executable-source update is still blocked by the normal tool safety path.

## Memory and Action Audit hardened-ordering follow-up

A schema-v1-compatible local SQLite reference prototype revalidated the intended transaction ordering without mutating persistent journal mode during ordinary opens.

Memory results:

- concurrent first-open: 20 callers x 10/10 rounds PASS;
- same-revision CAS: 20 callers x 20/20 rounds, exactly one winner and 19 domain conflicts each round;
- persisted content-digest tamper: fail-closed PASS;
- search ordering uses snapshot materialization -> persisted-row validation -> trusted-clock sample -> expiry filter;
- mutation/expiry cleanup uses write lock -> persisted-row validation -> trusted-clock sample -> revision/expiry-bound mutation.

Action Audit results:

- concurrent first-open: 20 callers x 10/10 rounds PASS;
- concurrent append: 30 callers x 20/20 rounds PASS;
- committed event timestamps stayed monotonic with event IDs in every contention round;
- persisted request identity was recomputed from tool/capability/scope/argument digest and tampering was rejected.

## Durable authorization entropy and atomic occurrence follow-up

A local SQLite reference prototype tightened the one-shot boundary so the trusted authorization component, not an arbitrary caller, creates bearer material.

Prototype properties:

- bearer material generated locally from 32 random bytes before URL-safe encoding;
- persisted token identity is a domain-separated SHA-256 digest only;
- authorization consumption and `execution_id` creation commit in one `BEGIN IMMEDIATE` transaction;
- `execution_id` is domain-separated and binds request identity plus token digest;
- consumed bearer plaintext is absent from database bytes.

Concurrency results:

- thread contention: 20 callers x 20/20 rounds, exactly one execution occurrence each round;
- process contention: 8 processes x 8/8 rounds, exactly one execution occurrence and zero infrastructure errors each round;
- bearer plaintext persistence check: absent in all prototype databases inspected.

The repository contract should therefore require trusted high-entropy bearer generation (or an equivalently strong keyed construction) before treating a stored token digest as protection against token recovery. An arbitrary low-entropy caller-supplied `token_id` must not become a durable bearer secret merely by hashing it.

## Repository and boundary status

No model training, Candidate generation, external GPU work, protected evaluation opening, promotion, main merge, or frozen-contract change occurred.

The next repository implementation order remains planner hardening, Memory durability/read ordering, Action Audit durability, reusable local-state migrations/startup recovery, then scheduler/observation source integration behind existing foundation contracts.
