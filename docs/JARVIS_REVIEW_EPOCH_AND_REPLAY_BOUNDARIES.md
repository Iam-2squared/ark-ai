# ARK JARVIS — Local Review Epoch and Replay Boundaries

Status: **research / reversible / disconnected / zero authority**, PR #8 Draft.
This is an implementation-oriented gap record. It is not a frozen contract,
security attestation, production permission, protected evaluation, or PASS.

## Three different facts must not be conflated

| Locally observed fact | What it supports | What it does **not** support |
| --- | --- | --- |
| An untrusted approval-claim envelope matches the Registry/action/request | Consistent locally claimed identity | Authenticated issuer, recipient, subject, purpose, nonce or consent |
| An append-only sidecar links that claim ID to a current reservation | A persistent, *untrusted* claimed pair | Proof approval existed when reservation was made; real ToolBackend effect |
| A recovered Planner step and ActionAudit agree with source/sidecar snapshots | Read-only diagnostic coherence | Atomic cross-store snapshot, exactly-once effect, automatic UNKNOWN WRITE retry |

`synthetic_claim_recovery_provenance_review.py` composes the existing
`synthetic_claim_recovery_review.py` and
`synthetic_claim_occurrence_recheck_review.py` reviewers. Its input names
one exact claim ID (via envelope) and **one** exact occurrence ID. It refuses
a missing association and deliberately refuses to classify multiple relevant
reservations as one unambiguous claim/occurrence provenance. It evaluates
claim/recovery, claim/source, claim/recovery, claim/source in that order and
rejects observed differences between rounds. Any matching result remains
deny-only: `human_consent_verified`, `dispatch_authorized`,
`automatic_replay_authorized`, and `external_outcome_known` are all false.

An optional earlier and **independently retained** source or link witness
can detect a truncated earlier local history. A witness generated from the
same already-modified database is **not** independent. Even repeated read-only
comparisons cannot close a race after the final check, authenticate the
caller-supplied clock, certify consent or attest remote/backend effects.

## Nested immutable diagnostic snapshots are not intrinsically immutable

Python `@dataclass(frozen=True)` restricts ordinary assignment, not
reflection through `object.__setattr__`. An outer tuple of nested dataclass
*references* can appear unchanged even if the nested field values are
modified during a callback. Security-sensitive before/after diagnostics must
pin the nested field **values**, not just object references.

- `personal_context_retention_recheck_review.py` now creates a value-only
  epoch over each `SyntheticRetentionItem` identifier/revision/state as well
  as the parent `SyntheticRetentionInventory` scalar fields. A caller
  swapping a nested item field during a later inventory read causes failure,
  even when the original item remains in the same tuple.
- `proactive_startup_fence_review.py` now pins the six scalar/nested fields
  of each `ComponentResult` and runs `StartupSnapshot._assert_integrity()`
  **after** the final scheduler-freshness callback. A READY snapshot edited
  after the last readiness lease is no longer accepted merely because its
  cached outer reference has not changed. The review still cannot authorize
  a notification or an actual ToolBackend execution.
- Requirement fields, clock epoch, receipt identity, policy, ledger path and
  observation/source digests remain bounded local inputs. A reflected change
  is evidence of a broken local diagnostic, **not** evidence of a hostile
  remote principal, and no real hardware or user interaction is involved.

Focused synthetic regression suites:
`tests/test_synthetic_claim_recovery_provenance_run381.py`,
`tests/test_personal_context_retention_nested_epoch_run381.py`, and
`tests/test_proactive_startup_nested_epoch_run381.py`.

## Remaining engineering gates

1. Recheck each exact GitHub branch HEAD through all supported Ubuntu/Windows
   Python 3.11–3.13 environments. Tests and prose cannot substitute for
   that evidence, and an earlier GREEN run does not certify a later SHA.
2. Implement **authenticated** issuer/subject/recipient/purpose/consent
   mechanisms, an appropriate trusted clock, protected revocation rights and
   independently retained append-history witnesses *before* any production
   grant. None is provided by these research modules.
3. Provide a real backend-specific idempotency/reconciliation design for
   externally ambiguous WRITE outcomes. An apparently successful local
   hash match does not prove real execution; `RUNNING` and UNKNOWN WRITE
   remain **never auto-replayable**.
4. Establish legal/privacy authorization and a separately approved deletion
   and backup lifecycle before irreversible personal-data erasure. Retention
   and revocation diagnostics are **read-only**.
5. Keep the V1/V2/Local UI/Launcher original paths and evidence frozen,
   V3 PR #5 Draft/NOT_PASSED, Candidate and protected FINAL gates closed.
   Avoid paid compute, new credentials, account integrations, physical-PC
   work, notifications, camera/mic/screen capture, and main merges.

This note records review boundaries and source-level intent. It makes no
claim that an in-progress CI run is GREEN.

## Memory v1 event-history continuity (read-only fixture)

`memory/synthetic_event_continuity_review.py` now evaluates one exact
`MemoryScope` in a pinned **read-only** SQLite transaction. It verifies the
unchanged Memory v1 schema, canonical scoped event rows and bounded
create/update/delete/expire lifecycle transitions against the current scoped
Memory records. Global `event_id` gaps are allowed because events from
different scopes interleave; caller timestamps are **not** falsely treated
as a trusted monotonic clock. Explicit deletion followed by a new
`create` at revision 1 for the same deterministic memory ID is distinct
from an invalid revision jump. No Memory content leaves the reviewer.

The returned content-minimized witness commits to the scoped event order,
event identities, revisions, operation types and local timestamps. An optional
**earlier independently retained** prefix detects truncation or rewriting
of that prior history even if the local event suffix and current Memory row
were rewritten coherently. Without such a retained witness, a coherent
rewrite of *all* affected local data can still pass: hashes are not external
attestations. The reviewer never grants personal-context use, disclosure or
deletion; it cannot guarantee backup erasure or cross-database atomicity.
No frozen Memory v1 DDL is changed.

Focused tests:
`tests/test_memory_synthetic_event_continuity_run381.py` exercises
CAS revisions, explicit delete/recreate, interleaved scope event IDs,
missing events or live rows, schema drift, missing-file no-recreation,
and independently retained-prefix rollback. Exact-head CI still governs
whether the implementation is platform-verified.
