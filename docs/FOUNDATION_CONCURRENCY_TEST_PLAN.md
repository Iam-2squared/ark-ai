# Foundation Concurrency Test Plan

Work basis: `ac2f15f03c1f15f22715c98f93ea680ced922b44`

This plan defines repeatable local concurrency evidence for ARK's durable foundations. It does not change any frozen contract, authorize external compute, or establish a roadmap PASS.

## Shared rules

- Use separate SQLite connections for competing workers.
- Include repeated rounds so a single lucky pass is not treated as concurrency evidence.
- Require domain-level conflict outcomes for expected contention.
- Treat raw SQLite lock/constraint errors as failures when the domain contract promises a deterministic conflict.
- Keep injected clocks deterministic.
- Record the exact code HEAD tested; prototype results are not repository evidence until the implementation is saved.

## Memory

Required stress cases:

1. concurrent first-open initialization;
2. concurrent create of the same deterministic memory identity, with exactly one winner;
3. concurrent update from the same observed revision, with exactly one winner;
4. purge racing a refresh, where a refreshed record must survive stale cleanup;
5. reopen after each mutation and verify persisted revision/content integrity.

The first three cases should be exercised with both threads and separate processes where practical.

## Action audit

Required stress cases:

1. concurrent first-open initialization;
2. concurrent appends from independent connections;
3. restart followed by ordered event readback;
4. same-version schema tamper rejection.

Append success must not depend on changing persistent journal mode during ordinary connection open.

## Durable one-shot authorization

Required stress cases:

1. concurrent first-open initialization;
2. many consumers racing one token, with exactly one successful consumption;
3. restart after consumption followed by replay rejection;
4. expiry boundary checks using the injected trusted clock;
5. schema/row tamper rejection.

Token plaintext must never be stored in the ledger.

## Planner journal

Required stress cases:

1. concurrent first-open initialization;
2. competing transitions from the same planner revision, with exactly one committed transition;
3. restart/replay to the same state and revision;
4. event deletion/reordering/modification detection;
5. recovered RUNNING state remains ambiguous and never causes automatic action replay.

## Proactive scheduler

Required stress cases:

1. competing workers evaluating the same trigger identity produce at most one prepared item;
2. restart preserves cooldown and deduplication state;
3. unchanged observations remain suppressed according to policy;
4. owner/namespace bindings cannot be widened by a competing worker.

## Evidence threshold

A useful pre-integration baseline is at least 20 repeated thread rounds for first-open/CAS paths and at least 5 repeated multi-process rounds for the highest-risk SQLite paths. Higher counts are appropriate before connecting real action adapters.

A stress result applies only to the exact tested implementation and does not replace normal unit tests, deterministic CI, frozen evaluation gates, or explicit authorization boundaries.
