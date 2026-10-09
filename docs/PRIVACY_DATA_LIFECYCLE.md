# ARK Privacy and Data Lifecycle

This document defines reversible, local-first privacy boundaries for JARVIS foundation work. It does not change any frozen V1/V2/Local UI/Launcher evidence, V3 Contract semantics, protected evaluation gates, Candidate state, or promotion authority.

## Core invariants

- Personal data is local-first by default. No foundation work may require a paid or external service.
- Every persisted memory belongs to one exact owner and namespace. Cross-owner or cross-namespace reads fail closed.
- Persisted rows are treated as untrusted input and must pass identity, digest, metadata, timestamp, revision, and scope validation before they can be surfaced or mutated.
- Provenance and action audit records should store deterministic identifiers and hashes instead of unnecessary plaintext.
- Expired data is hidden from normal retrieval immediately and is physically deletable.
- Deletion and expiry purge must be compare-and-delete safe so a concurrently refreshed record cannot be removed by a stale cleanup operation.
- Retention behavior must be explicit. Permanent retention is never inferred from missing evidence or an ambiguous policy.
- Schema version alone is insufficient trust. Same-version stores must validate expected tables, columns, constraints, and indexes before use.
- Clock rollback, malformed timestamps, invalid revisions, and identity/hash mismatches fail closed rather than being silently repaired.

## Data classes and lifetimes

### Memory content
Memory content is the user-facing payload. It may be retained only within its explicit owner/namespace scope and optional expiry. Search/retrieval must never widen scope implicitly.

### Memory metadata
Metadata is part of the integrity boundary. Canonical serialization is required before hashing or persistence. Unknown or malformed persisted metadata is rejected.

### Memory events
Lifecycle events record operation, memory identity, scope, revision, and time. They must not duplicate full memory plaintext.

### Personal-context provenance
Context provenance binds the memory identity, revision, and content digest that produced a context item. Provenance should remain useful for replay/debugging without embedding the underlying plaintext.

### Action audit
Action audit stores request identity, tool/capability/scope, argument digest, outcome, and time. Raw tool arguments are excluded unless a later explicit contract requires a narrowly-scoped exception.

## Required lifecycle operations

1. **Create**: deterministic identity, revision 1, canonical metadata, integrity digest.
2. **Update**: exact expected revision, prior-row integrity validation, monotonic trusted time.
3. **Read/Search**: exact owner/namespace match, persisted-row integrity validation, expiry filtering.
4. **Delete**: exact expected revision and current-row validation before physical deletion.
5. **Expire/Purge**: conditional delete bound to the observed revision and expiry predicate.
6. **Recovery/Open**: atomic initialization, same-version schema validation, no silent downgrade or auto-repair of unknown schema.

## Concurrency requirements

- First-open initialization must be safe under concurrent processes.
- Compare-and-swap updates allow exactly one winner for a given observed revision.
- Concurrent create of the same deterministic identity yields one record; losers receive a domain conflict rather than raw SQLite integrity errors.
- Expiry cleanup may not delete a record that was refreshed after the cleanup reader observed it.

## Data export and external boundaries

No personal-memory or action-audit export is implied by this foundation. Any future connector, cloud sync, telemetry, or external model path must introduce an explicit contract for purpose, fields, destination, retention, and user authorization before data leaves the local boundary.

## Integration rule

These lifecycle rules are foundation constraints, not roadmap PASS evidence. They do not authorize paid/external compute, Candidate generation, protected evaluation opening, promotion, frozen-contract changes, destructive actions, new credentials, physical-device control, or main merge.
