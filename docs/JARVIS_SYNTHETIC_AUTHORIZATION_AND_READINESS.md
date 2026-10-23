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
