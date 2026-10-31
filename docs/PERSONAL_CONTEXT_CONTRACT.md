# ARK Personal Context Contract

Work basis: `6d19a210be4936f818fd015e74b6ee94d12fd1c4`

This contract defines the reversible local-first layer that turns validated Memory records into a bounded context bundle for reasoning. It does not create new Memory authority, external sync, paid services, or action permissions.

## Scope boundary

Every retrieval request binds one exact owner and an ordered set of explicitly requested namespaces.

Rules:

- no cross-owner retrieval;
- no implicit parent, prefix, wildcard, or neighboring namespace expansion;
- an unknown namespace yields no records rather than widening scope;
- expired, deleted, schema-invalid, or integrity-invalid records are never surfaced;
- Personal Context never bypasses the Memory store's row validation or retention rules.

## Request contract

A context request declares at least:

- owner identity;
- ordered namespace list;
- query text or retrieval intent;
- total item budget;
- optional per-namespace budget;
- retrieval-policy revision.

Budgets are exact positive non-bool integers. Duplicate namespaces are rejected or normalized deterministically before retrieval; unordered namespace containers are not accepted.

## Deterministic retrieval

For one exact persisted Memory state and one exact request, retrieval order must be deterministic.

The Personal Context layer may rank records using Memory's deterministic retrieval score, but it adds a cross-namespace fairness step so one namespace cannot consume the entire bundle merely because it contains more matching rows.

The initial policy is deterministic round-robin across the ordered requested namespaces:

1. obtain an independently ranked candidate list for each namespace;
2. take at most one candidate from each namespace per round;
3. continue rounds until the total budget is exhausted or all lists are empty;
4. never reorder candidates within one namespace.

A future policy may change this behavior only under a new explicit policy revision.

## Provenance

Every surfaced context item carries content-free provenance sufficient to explain and reproduce selection:

- memory identity;
- memory revision;
- content digest;
- owner/namespace identity;
- retrieval-policy revision;
- deterministic ordinal in the final bundle.

The provenance identity is derived from canonical serialization of those fields. It does not include Memory plaintext.

A changed revision, digest, namespace, policy revision, or ordinal changes the provenance identity.

## Bundle identity

A context bundle has a deterministic identity derived from:

- request identity;
- ordered provenance identities;
- retrieval-policy revision.

Equivalent bundles produce the same identity. The bundle identity is provenance only; it is never a capability grant, one-shot authorization, or permission to retain source content beyond Memory's lifecycle.

## Integrity and duplication

The layer fails closed if:

- a returned record's owner/namespace differs from the requested scope;
- duplicate memory identities appear in one candidate set or final bundle;
- the same memory identity appears with conflicting revisions/digests;
- a record becomes expired or fails integrity validation before bundle construction completes;
- persisted provenance has malformed identity/revision/digest fields.

## Retention

A context bundle is a derived view, not a second long-term memory database.

By default:

- bundle plaintext is ephemeral;
- durable traces keep bundle/provenance digests and counts rather than copied Memory content;
- deleting or expiring source Memory prevents that source from appearing in newly built bundles;
- no external export is implied.

If a later feature needs durable context snapshots, it requires an explicit purpose, retention period, deletion behavior, and privacy review.

## Planner and proactive use

Planner, proactive scheduler, voice, vision, and UI flows may request a Personal Context bundle, but the bundle supplies information only.

It cannot:

- create or widen a capability grant;
- mint or consume one-shot authorization;
- change planner state;
- authorize computer control;
- override retention/deletion;
- justify paid/external execution.

Any resulting action still passes through the common ToolRegistry, capability, durable authorization, audit, and execution boundary.

## Required tests

Repository implementation must cover at least:

- exact owner isolation;
- exact namespace isolation;
- deterministic ordering across randomized insertion order;
- round-robin fairness across multiple namespaces;
- total and per-namespace budget boundaries;
- expired-record exclusion;
- integrity/tamper rejection inherited from Memory;
- duplicate identity/conflicting revision rejection;
- deterministic content-free provenance;
- bundle identity stability;
- bool/zero/negative budget rejection;
- no plaintext in durable provenance representation.

## Integration order

1. land Memory schema/integrity/concurrency/retention hardening;
2. implement immutable Personal Context request/result/provenance contracts;
3. implement deterministic multi-namespace retrieval over the Memory interface;
4. add restart-independent fixture tests and randomized insertion-order tests;
5. integrate read-only context bundles into planner/UI/proactive paths;
6. keep write actions behind the separate agency authorization boundary.

This foundation is not a roadmap PASS and changes no frozen V1/V2/Local UI/Launcher evidence, V3 Contract, protected evaluation gate, Candidate state, promotion authority, paid-service boundary, or main-merge requirement.
