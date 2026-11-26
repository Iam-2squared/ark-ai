# Memory Coherent Snapshot Contract

Status: reversible source contract for Draft PR #8. This is not roadmap PASS evidence.

Work basis: `9565220a84d273d1d3148fe21416bd799485df67`.

## Purpose

Personal Context and later proactive reasoning need to read several Memory namespaces without creating a bundle that mixes database states from different moments.

A coherent snapshot operation is therefore part of the Memory boundary rather than a best-effort behavior in higher-level context assembly.

## Request

A snapshot request binds:

- one exact owner identity;
- an ordered, duplicate-free tuple of namespaces;
- an exact non-bool per-namespace limit;
- whether expired records are eligible;
- the query text used for deterministic ranking.

Unordered namespace containers are rejected so caller intent and bundle ordering cannot depend on hash iteration order.

## Snapshot semantics

All requested namespaces are read and fully materialized inside one short SQLite read transaction.

The implementation must not:

- open a separate connection per namespace;
- commit between namespace reads;
- lazily fetch rows after the transaction closes;
- widen the owner or namespace set;
- mutate persistent journal mode on ordinary read connections.

Concurrent writers may commit while the snapshot transaction is open, but every namespace in one result must observe one SQLite snapshot.

Trusted-time expiry filtering uses one validated timestamp for the whole snapshot so records are not classified against different clock samples inside one bundle.

## Validation before exposure

Every persisted row is untrusted until validation succeeds.

Before a row enters the snapshot result, Memory must validate its canonical identity, scope, source identity, content digest, metadata representation, exact persisted storage classes, timestamps, expiry, and revision.

One malformed eligible row fails the snapshot closed rather than silently dropping corruption and presenting a partial context view.

## Deterministic result

Within each namespace, ranking uses the existing deterministic search rules and stable tie breakers. Results preserve the caller's namespace order.

The snapshot result should carry content-free provenance sufficient for higher layers to bind:

- memory identity;
- owner and namespace;
- revision;
- content digest;
- update timestamp;
- snapshot trusted time.

The Memory layer does not interpret plaintext as instructions and does not grant action authority.

## Concurrency acceptance tests

Repository tests must demonstrate:

- a writer committing between two namespace reads cannot produce a mixed-time bundle when the coherent API is used;
- repeated equivalent requests return equivalent ordered identities when the database state is unchanged;
- owner and namespace isolation remain exact;
- malformed persisted rows fail closed;
- one trusted time sample governs expiry across the full snapshot;
- no write lock or persistent journal-mode transition is required for normal coherent reads.

## Integration rule

Personal Context should depend on this API rather than looping over the existing single-namespace `search()` method.

This contract adds no external compute, paid service, Candidate work, protected evaluation access, computer-control authority, frozen-contract change, or main-merge authority.
