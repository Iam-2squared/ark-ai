# Disconnected recovery triage and proactive fixture review

**Status:** Draft PR #8, reversible, offline-only engineering. This document
describes research code in `src/ark/agency/synthetic_recovery_triage.py`,
`src/ark/proactive_synthetic_review.py`, and
`src/ark/personal_context_review.py`. It does **not** modify normative or
frozen contracts and does **not** authorize execution, notification or data
export. Exact-head CI GREEN must be verified separately.

## P0 — cross-store synthetic WRITE recovery diagnostics

`review_synthetic_write_recovery` accepts an existing synthetic plan journal,
an already-initialized synthetic occurrence ledger, an already-initialized
SQLite action audit, an exact ToolRegistry and ToolCall, and a plan step ID.

The routine:

1. Rebinds the requested call against the registry and requires a WRITE
   registration. It compares the request ID with the chosen plan step.
2. Replays the planner's existing synthetic journal, optionally comparing
   an independently retained older `SyntheticPlanTail`.
3. Inspects all bounded reservation rows from **one read-only SQLite
   snapshot**; verifies exact v1 schema/rows, builds a corresponding ledger
   witness from those same rows, and compares an optionally retained witness.
   A request observed with a different registry/action binding is rejected.
4. Reviews the independent audit store's persisted chain with optional
   historical prefix evidence, and requires nondecreasing caller timestamps.
5. Rebinds registry identity before returning an **inert** report.

The report exposes the step state, whether an interrupted `RUNNING` WRITE
is ambiguous, plan tail, content-free ledger witness, audit witness, and
matching synthetic occurrence identifiers. Its `dispatch_authorized`,
`automatic_replay_authorized` and `external_outcome_known` values are always
`False`. Even `SUCCEEDED` in Planner, a matching synthetic reservation,
and a matching audit history **cannot establish an external effect**.

**Crucial limitation:** plan, ledger and audit are read in **three separate
transactions**, not one globally atomic snapshot. They may change between
reads. Audit events do not have an authenticated occurrence binding. In
addition, an earlier hash witness is only useful if genuinely retained
outside the mutable store. This review must never become an executor gate
that treats apparent consistency as authorization. Missing files, malformed
schema, historical rewrites and conflicting registry identities fail closed.

No raw tool arguments, plaintext bearer token, live backend, or network
service is read or invoked by this reviewer.

## P1 — content-minimized synthetic proactive admission

`SyntheticProactiveLedger` is a small SQLite **fixture**, not a scheduler
service. It hashes the supplied exact owner, namespace, trigger definition,
definition revision, and policy into local scope/policy identities. A trigger
instance further binds the SHA-256-formatted source and observation digests.
The row stores only these content-minimized identities and two timestamps.

Under `BEGIN IMMEDIATE`, `prepare` verifies exact version-1 fixture
schema and persisted row shapes, rechecks the pinned policy input, and
enforces:

- duplicate trigger identity exclusion across restarts and concurrent
  independent store handles;
- minimum preparation interval for the same scope/policy;
- a bounded maximum number of **preparations** in a rolling time window;
- caller-clock rollback refusal and rejection of future-dated observations;
- atomic insertion of one `prepared` marker, with no external action.

The window is half-open: a preparation at time `t` occupies the window
while `t > now - rolling_window_ms`. The maximum stored fixture budget is
10,000 rows per review. A policy version change deliberately changes local
identity; it does **not** establish that an authorized user approved new
limits. Every `SyntheticTriggerReceipt` has
`notification_authorized=False`, `dispatch_authorized=False` and
`automatic_replay_authorized=False`.

**Crucial limitations:** caller-supplied time is not trusted time. SQLite
storage and local SHA hashes are not independently attested. Storing digests
instead of raw values reduces content retention but may not prevent
dictionary attacks on low-entropy owner/namespace identifiers. No
multi-process service lifecycle, notification budget, user consent,
reconciliation, observation capture, or external WRITE is implemented.
There is no assertion that synthetic admission equals a live proactive agent.

## P1 — ephemeral Personal Context projection

`src/ark/personal_context_review.py` accepts a previously produced
`CoherentSnapshotReview`, whose Memory rows came from one local SQLite read
snapshot and clock sample. It validates exact owner/namespace scope, canonical
Memory identities, revisions, timestamps, expiration at the snapshot clock,
and content SHA-256 before selecting anything. It refuses duplicates across
namespaces or conflicting records instead of silently widening a scope.

A bounded, immutable `ContextSelectionPolicy` sets total and per-namespace
caps. Already-ranked candidates are selected by deterministic round-robin
across caller-ordered namespaces, preserving each namespace's source order.
Content remains **ephemeral information**; only record identities, revisions,
content digests, policy revision and selection ordinal enter content-free
provenance identifiers and the bundle identifier. Instruction-like text is
returned as untrusted data rather than executed. The result's
`dispatch_authorized` and `action_authorized` flags are always false.

**Privacy limitation:** the projection is fresh only at the **original**
coherent snapshot timestamp. It does not re-open Memory when a later
revocation, deletion, consent withdrawal or expiry occurs. Callers must obtain
a fresh coherent snapshot before reusing data in a later request. Local
SHA-256 IDs are not issuer authentication or externally trusted provenance.
There is no direct UI, model, scheduler or tool integration.

## P1 — audit SQLite connection lifecycle

The existing `SQLiteActionAudit` fixture used sqlite3's connection context
manager for bootstrap and append transactions. That context manager commits
or rolls back but does **not** necessarily close the underlying file handle.
Both writer and bootstrap paths now explicitly close their connections after
transaction exit. This preserves the fixed ActionAudit v1 schema and
append semantics, but makes local file relocation/replacement and failed
transaction cleanup deterministic on Windows.

Focused regressions cover successful bootstrap, successful append, failed
clock callback rollback, rejection of unsupported schema versions, and
no accidental recreation of an unavailable audit path. This is local file
descriptor hygiene, not an external audit attestation or permission grant.

## Readiness and integration order

Both packages remain separated from actual tool execution. Before any real
action or real notification can even be proposed for enablement, the system
still needs issuer-authenticated user consent, exact purpose/recipient
binding, trusted clock, durable occurrence-to-audit identities, backend
idempotency and unknown-outcome reconciliation, privacy erasure semantics,
startup readiness, and explicit user approval. Those gates are not supplied
by these fixtures.

The focused regressions cover real SQLite restarts, input boundaries,
same-database races, retained-history failures, stale or missing databases,
Windows-compatible file handling and disabled-dispatch properties.
Results must be reported by exact code/test HEAD and CI job conclusions;
unverified or still-running CI is not GREEN.

Frozen V1/V2/Local UI/Launcher evidence, V3 Draft PR #5's NOT_PASSED gate,
protected evaluations, paid compute, Candidate promotion and protected main
merge remain untouched.
