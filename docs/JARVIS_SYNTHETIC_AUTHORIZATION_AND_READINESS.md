# JARVIS foundation integration boundary — synthetic authorization / readiness

**Status:** disconnected, reversible engineering research. This document defines
negative guarantees and the promotion gate; it is **not** a production authority
or evidence of human review, consent, or execution.

## Components and their exact boundaries

| Component | What its local checks establish | What they do **not** establish |
| --- | --- | --- |
| `agency/registry.py` | deterministic ToolCall binding to a checked registry revision and backend identity | trusted plugin code, malicious in-process mutation resistance, runtime sandbox |
| `agency/policy.py` | matching exact-scope grants and process-local one-shot token spend; all policy input epochs rechecked under the token lock | issuer authenticity, human consent, durable/restart-safe token consumption, real WRITE authority |
| `agency/durable_occurrence_review.py` | persistent **synthetic** token/occurrence uniqueness via one SQLite `BEGIN IMMEDIATE` transaction; replay rejected after restart and between fixture store instances | actual issuance, signing, trusted time, credentials, audit-before-action, remote idempotency, exactly-once external effects |
| `startup_readiness_review.py` | deterministic dependency propagation for supplied synthetic probes, and local checksum revalidation before reading a cached diagnostic snapshot | authenticated hardware/store/backend probe, attested state, activating any capability |

`SyntheticReservationReceipt.dispatch_authorized`,
`automatic_replay_authorized`, and `outcome_known` are always **False**.
The SQLite file is a *fixture*. Its integrity validation is local and can be
defeated by an actor allowed to rewrite all storage and checksums. SHA-256
digests and registry revisions must never be described as an issuer signature
or evidence that a human approved an action.

The fixture stores a SHA-256 token digest rather than plaintext token. This
is **not** a password-hashing or secret-management scheme. Use only artificial,
nonsecret, high-entropy test identifiers. Do not store real access credentials.

## Additional disconnected integrity reviews (Run 369)

The synthetic reservation fixture also validates every persisted row on open,
observation and new reservation. It requires canonical token/occurrence/
registry/action/request identifiers, exact signed-64-bit times with
`0 <= reserved_at_ms < expires_at_ms`, and a bounded 10,000-row review budget.
This rejects many same-schema malformed rows that a SQLite `quick_check`
alone cannot classify. It **cannot** establish that a well-formed historical
row belongs to a trusted issuer or that an attacker did not replace it with
another valid-looking row.

`agency/synthetic_occurrence_continuity_review.py` is a separate **read-only**
witness reader. It hashes each canonical persisted reservation row, records a
sorted local row-digest set, and compares an independently retained prior
witness with the current snapshot. Append-only growth passes; deletion or
rewrite of a retained row fails. This is meaningful **only if the earlier
witness was preserved outside the mutable SQLite database**. Neither a local
checksum nor a witness recomputed after corruption is an attestation. Raw
bearer tokens and ToolCall argument payloads are not emitted.

The startup readiness snapshot now checks structural consistency and
re-derives every effective dependency state before returning a cached
diagnosis, even if a changed local digest has been recomputed. A fully
rewritten, internally consistent fake snapshot can still pass; no real
hardware, registry, user or backend readiness is authenticated.

`PlanGraph.topology_digest()` and `PlanGraph.status_digest()` provide
canonical local planner identities for later **replay-only** engineering:
ordered step IDs, canonical request IDs and dependency tuples bind topology;
the full status witness includes derived terminal-blocked revisions.
They do not persist journal events, certify a trusted clock, guard concurrent
`PlanGraph` mutation or give authority to restart an interrupted WRITE.

## Run 370 — additional synthetic clock and audit diagnostics

`SyntheticOccurrenceStore.reserve_synthetic()` now rejects a caller-supplied
reservation time earlier than the latest committed reservation time **inside
the same SQLite write transaction**. Identical timestamps remain allowed.
This is a lower bound on the local fixture's observed time, **not** trusted
clock evidence: deleting/replacing the ledger can erase the lower bound,
and an arbitrary caller-supplied time may still be false.

The existing read-only `review_audit_continuity()` now also accepts an
**opt-in** `require_monotonic_time=True`, rejecting event timestamps that
move backwards across the reviewed SQLite snapshot. The default review
semantics remain unchanged. Chronological consistency is neither provenance
nor external clock attestation, and the audit store is not transactionally
joined to the synthetic reservation or Planner journal.

The separate `SyntheticPlanJournal` fixture records canonical explicit plan
state transitions with an internal atomic hash-chain tail. Its opt-in earlier
`SyntheticPlanTail` comparison requires a genuinely independently retained
witness to detect a coordinated valid-looking tail rewrite. Recovery reports
interrupted RUNNING steps as ambiguous and never authorizes replay, dispatch
or real-world action. All three safeguards remain synthetic/disconnected.

## Fail-closed crash and replay reasoning

1. A caller supplies an artificial registry, ToolCall, OneShotAuthorization,
   occurrence identifier and caller-provided time.
2. The fixture checks their identity, WRITE effect, token/request match and
   supplied expiry; no real issuer or clock authority is inferred.
3. SQLite acquires `BEGIN IMMEDIATE`, validates the fixture schema, rebinds
   the exact action, and inserts an occurrence/token uniqueness row.
4. Only a committed transaction yields an inert receipt. Duplicate token OR
   duplicate occurrence is rejected, including on a later process.
5. A crash before commit leaves no reserved row. A crash after commit may leave
   a reserved row without any known action outcome. **Never replay a real
   external WRITE from this evidence.** No external WRITE is performed by
   this module in either case.
6. A corrupt or schema-mismatched database is rejected; the fixture does not
   migrate, auto-repair, truncate, or create a replacement during read-only
   observation. A local file can still be deleted or replaced by another actor.

This property is **at-most-one durable synthetic reservation per persisted
database identity**, not exactly-once action execution. True external
exactly-once semantics require an idempotent backend protocol and reconciliation
with independently verified transaction/outcome evidence. Those pieces remain
unimplemented and gated.

## Promotion blockers (all mandatory)

- Trusted and explicit issuer/subject/approval/expiry evidence tied to the
  exact ToolRegistry revision, canonical bound action, capability, scope,
  occurrence, privacy purpose and recipient.
- A trustworthy clock and an audit-before-action reservation whose atomic
  boundaries and storage failure modes are documented and fault-injected.
- A durable authorization store with independently retained continuity evidence,
  concurrent-process crash/restart tests and a defined `UNKNOWN` outcome state.
- An isolated mock executor that proves denial, replay, expiration, cancellation
  and partial-failure paths without invoking any real backend.
- Backend-specific idempotency/reconciliation before any real write, then
  explicit user approval for connecting or enabling affected capabilities.
- Exact-HEAD CI GREEN across the repository matrix after all dependencies are
  connected. A pass on one component's test HEAD never certifies a later HEAD.

## Frozen and financial boundaries

All V1/V2/Local UI/Launcher evidence and protected evaluation contracts remain
unchanged. V3 PR #5 stays Draft / NOT_PASSED. No paid or potentially billable
service, external GPU, model training/Candidate generation, protected final
evaluation, real tool action, credentials, account connection, notification,
promotion or main merge is authorized by this research.
