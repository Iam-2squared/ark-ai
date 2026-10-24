# ARK JARVIS — Claim/Occurrence Provenance Gap (research-only)

Status: **DRAFT / disconnected / non-authorizing**. This is a test and implementation
contract proposal, not a frozen contract, verified human approval or a migration
decision. It applies only to added-only JARVIS research modules in PR #8.
Frozen V1/V2/Local UI/Launcher evidence and V3 PR #5 gates remain unchanged.

## Observed gap in source

`synthetic_claim_recovery_review.py` verifies that an untrusted approval claim,
the immutable ToolRegistry binding and read-only Planner/occurrence/audit
snapshots agree on **Registry revision, bound Action ID and request ID**. A
reservation in `durable_occurrence_review.py` stores its one-shot token digest
and occurrence identity, but **does not persist the approval claim ID,
issuer/subject/purpose/recipient/nonce digests, or a verification record of
their authority**. Two different locally coherent claims for the same
request can therefore both describe the same reservation in a diagnostic
review. A matching cross-store receipt **must not be named proof of historical
approval-to-occurrence provenance**.

The existing `SyntheticClaimRecoveryReview` correctly exposes
`human_consent_verified=False`, `dispatch_authorized=False`,
`automatic_replay_authorized=False`, and `external_outcome_known=False`.
A stored cancellation marker is a veto, **not proof that absent cancellation
means consent**. None of the SQLite witnesses are externally authenticated.

## Proposed reversible FREE-only evidence lane

A **new, isolated, create-only synthetic sidecar** (NOT a modification to the
frozen ActionAudit schema or existing occurrence reservation table) can record a
one-to-one *claimed local association* of:
- exact `approval_id`, canonical `nonce_digest`, issuer/subject/purpose/
  recipient digests, and issued/expiry clocks from the existing envelope;
- exact `registry_revision`, `bound_action_id`, `request_id` and
  `occurrence_id` from the already committed reservation;
- the reservation's independently reviewed row hash/witness and the
  cancellation journal's observed tail, labeled as local, untrusted evidence;
- a deterministic, domain-separated append identity, previous event hash,
  sequence number and local append timestamp.

A sidecar record is a **claim** about two local objects; it is not an
authenticated signature, user approval, token consumption, transactional
cross-store commit, external outcome proof, or execution permit.

Admission and read-only review should reject **any** mismatch, missing
reservation, claim expiry, cancellation, invalid SQLite schema, forged
receipt, duplicate occurrence, duplicate claim association, changed history,
timestamp rollback, and reflected input drift. Optionally compare a
**genuinely earlier and independently retained** prefix witness. Replay of
the current DB to regenerate its own witness is not independent evidence.

## Acceptance matrix for an isolated implementation

| Fixture | Required result |
| --- | --- |
| Correct offline claim + one persisted matching reservation | Inert identity-only evidence |
| Same request, different claim nonce/purpose/recipient | Different identity; never interchangeable |
| Duplicate claim, occurrence, or cross-association | Reject atomically before append |
| Cancelled claim or veto added during review | Reject; no dispatch or replay |
| Claim expires at the admission clock | Reject at open upper expiry bound |
| Missing/renamed SQLite source or sidecar | Refuse without creating a replacement |
| Schema version, extra trigger/index or persisted row tamper | Reject |
| Earlier separately retained witness no longer matches | Reject |
| Crash before/after sidecar commit | Recover as distinct known local states |
| UNKNOWN real WRITE outcome with all local evidence matching | **Still UNKNOWN, never auto-retry** |
| Backend, notification, camera/mic/screen or external GPU request | Not in this lane; never executed |

All mutation transactions must use SQLite's ordinary safe, documented
transaction APIs. No raw Git-object writes, force pushes, paid compute,
credentials, model training, protected evaluation, automatic promotion,
physical-PC actions or actual network/backend dispatch.

## Dependencies before any later integration

1. Exact-head CI GREEN for existing Registry, PermissionGate, durable occurrence,
   ActionAudit, Planner recovery and cancellation reviewers.
2. A separately reviewed, provenance-preserving approval producer with
   authenticated issuer, subject, recipient and purpose. This does **not** exist.
3. Trusted clock, revocation rights, independently protected evidence and an
   explicit treatment of races after final local review. These do **not** exist.
4. External backend effect/idempotency reconciliation for UNKNOWN WRITE and
   human authorization for real effects. These do **not** exist.

Until the actual authorities and evidence exist, any prospective implementation
must permanently return false for human consent, dispatch, replay and known
external outcome. The work may move forward offline without declaring PASS.
