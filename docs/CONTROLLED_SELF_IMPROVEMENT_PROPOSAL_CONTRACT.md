# Controlled Self-Improvement Proposal Contract

Status: reversible proposal-only foundation for Draft PR #8. This is not Candidate promotion authority and not roadmap PASS evidence.

Work basis: `8f840b48e49fad231929c0988b479b10bf0a941a`.

## Purpose

ARK may eventually detect recurring weaknesses and prepare improvement proposals, but proposal generation must remain separate from training, evaluation opening, Candidate generation, promotion, and code modification.

The initial foundation is therefore proposal-only.

## Proposal identity

Each proposal binds:

- proposal schema version;
- stable issue/category ID;
- source evaluation or observation identities;
- exact affected component or capability;
- content-free provenance digests;
- proposed change class;
- proposal-policy revision.

Equivalent inputs under the same policy produce the same proposal identity.

## Allowed proposal classes

Initial proposal classes are descriptive only:

- add or strengthen a test;
- investigate a repeated failure pattern;
- improve local retrieval/context selection;
- propose a planner/tool contract change for review;
- propose a future training/evaluation experiment without running it.

A proposal does not itself modify source, datasets, weights, frozen contracts, evaluation gates, or runtime permissions.

## Evidence boundary

The proposal store retains only the minimum evidence required to explain why the proposal exists. Raw private Memory content, raw media, bearer credentials, and full tool arguments are excluded by default.

When a proposal cites Memory-derived evidence, it uses owner/namespace-isolated content-free provenance and exact memory identities/revisions/digests.

## Lifecycle

Suggested states:

1. PROPOSED;
2. REVIEW_REQUIRED;
3. ACCEPTED_FOR_IMPLEMENTATION;
4. REJECTED;
5. SUPERSEDED.

State transitions are durable and revision-guarded. ACCEPTED_FOR_IMPLEMENTATION means only that normal development may begin under the existing repository and authorization rules.

It never means Candidate promotion, protected evaluation opening, or permission to spend money.

## Deduplication

Repeated detection of the same issue under the same proposal-policy revision updates occurrence evidence rather than creating unbounded duplicate proposals.

A materially changed source identity, affected component, or policy revision creates a new proposal identity.

## Integration

Proposal generation may consume:

- deterministic evaluation summaries;
- observability counters;
- planner recovery failures;
- startup-readiness failures;
- explicit user feedback;
- content-free Personal Context provenance when appropriate.

It does not consume protected evaluation material unless that material has already been explicitly opened under its own gate.

## Tests required

Repository tests should cover:

- deterministic proposal identity;
- input-order independence;
- duplicate suppression;
- owner/scope provenance isolation;
- durable revision conflicts;
- proposal creation having no side effect on ToolRegistry permissions;
- proposal acceptance not changing Candidate/promotion/evaluation authorization.

## Hard boundary

No proposal path may automatically:

- edit frozen contracts;
- start external compute;
- generate or promote Candidate weights;
- open protected V2 evaluation;
- merge to main;
- connect credentials/accounts;
- execute computer actions.

Those remain governed by their existing explicit gates.
