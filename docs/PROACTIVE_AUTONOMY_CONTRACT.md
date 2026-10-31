# Proactive Autonomy Contract

Work basis: `bce89b4df715ea52935f7e45473c2f225da50b22`

This document defines a reversible, local-first boundary for proactive ARK behavior. It does not authorize paid services, external compute, real Candidate generation, protected evaluation opening, promotion, computer control, or main merge.

## Goal

Allow ARK to notice locally observable conditions and prepare useful work without turning observation into ambient authority.

A proactive cycle is split into four explicit phases:

1. **observe** — collect already-authorized local signals;
2. **decide** — determine whether the signal is actionable under a deterministic policy;
3. **prepare** — build a plan, context bundle, or user-facing proposal;
4. **act** — execute only through the existing capability, authorization, audit, and planner boundaries.

Observation and preparation never imply permission to perform a side effect.

## Trigger identity

Every trigger instance must have a deterministic identity derived from:

- trigger definition ID and revision;
- owner/namespace scope;
- canonical source identity;
- canonical observation digest;
- policy revision.

Raw private payloads should not be embedded in trigger IDs or audit correlation keys.

Equivalent observations under the same trigger revision must deduplicate to the same trigger identity. A changed observation or policy revision must produce a different identity.

## Local-first scheduler state

Scheduler state should be persisted locally and contain only the minimum data needed for deterministic recovery:

- trigger definition ID/revision;
- last evaluated observation digest;
- last decision;
- next eligible evaluation time;
- deduplication/cooldown state;
- planner request identity when a plan was prepared;
- content-free provenance needed to explain the decision.

The scheduler must not persist raw microphone/video frames, raw tool arguments, secrets, or duplicated Personal Context plaintext unless another explicit retention contract requires it.

## Rate and attention budgets

Each trigger definition must declare bounded evaluation and notification policy. At minimum:

- a minimum evaluation interval;
- a cooldown after a surfaced notification;
- a maximum surfaced-notification count per rolling window;
- whether unchanged observations are suppressible;
- whether the trigger may prepare work while notifications are suppressed.

Invalid or missing limits fail closed.

These limits are product-safety and resource-budget boundaries, not model suggestions. A model may recommend a different cadence but cannot silently override the persisted policy.

## Side-effect boundary

Proactive execution must use the same action pipeline as interactive execution.

A prepared write-effect action must still require:

- an immutable registered tool/capability mapping;
- an active capability grant for the exact scope;
- restart-safe one-shot authorization bound to the exact request;
- trusted-clock expiry evaluation;
- a successful pre-action audit write;
- replay protection;
- planner revision agreement when the action belongs to a plan.

No scheduler state, model output, notification acknowledgment, or prior successful action can substitute for these requirements.

## Recovery

After restart, ARK may safely resume observation and re-evaluate triggers from persisted scheduler state.

Recovery must never infer that an external side effect completed merely because a trigger was marked prepared or a planner step was `RUNNING`.

Unresolved write-effect work remains ambiguous until reconciled through durable request identity, action audit, and backend-specific idempotency/reconciliation rules. Automatic blind replay is forbidden.

## Personal Context use

A trigger may retrieve Personal Context only through explicit owner/namespace scopes and the existing retention/integrity rules.

Trigger evaluation must retain provenance sufficient to identify which memory identities/revisions influenced a decision without copying their plaintext into scheduler metadata.

Expired, deleted, cross-owner, cross-namespace, or integrity-invalid memories must not be surfaced to a proactive decision.

## Notification semantics

Notifications are observations surfaced to the user, not authorization tokens.

A notification should bind:

- trigger identity;
- reason category;
- prepared plan/request identity when present;
- content-free provenance;
- creation and expiry times.

Acknowledging or opening a notification does not grant a write-effect capability unless a separate authorization flow explicitly does so.

## Determinism and testing

The foundation should be testable with an injected trusted clock and mock/disconnected sources/backends.

Required tests include:

- deterministic trigger identity and deduplication;
- cooldown/window boundary behavior;
- restart recovery;
- unchanged-observation suppression;
- owner/namespace isolation;
- expired/tampered Personal Context rejection;
- notification acknowledgment not becoming authorization;
- concurrent scheduler evaluation producing at most one prepared item for one trigger identity;
- no automatic replay of ambiguous write-effect work.

## Integration order

1. land planner, Memory, durable authorization, action-audit, and ToolRegistry hardening;
2. add a local scheduler state store with strict schema validation and CAS;
3. integrate read-only/mock observation sources;
4. integrate Personal Context retrieval by explicit scope;
5. emit proposal/notification artifacts only;
6. connect write-effect execution only through the established authorization/audit pipeline.

This foundation is not a roadmap PASS and does not authorize autonomous real-world side effects.
