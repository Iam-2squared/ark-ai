# ARK JARVIS — Run534: Memory CAS expiry/clock + detached failure archive

Status: **Draft, reversible, disconnected, NOT_PASSED**. Recorded 2026-11-02 JST.
This is an implementation/evidence note, not model training, human review,
trusted-clock attestation, real ToolBackend execution, or main-merge permission.

## Exact work basis and commits

- Initial PR #8 branch HEAD: `1b2a7c05211cfab59a6bc28e0620dfaa41e559a9`.
- Memory implementation: `afb3e918d7995ff66067c11e61556870813255ad`.
- Memory focused tests: `d49354cab574cfdc2bb8866764832b917068ad14` (12 authored parametrized cases).
- Disconnected failure archive implementation: `e8921eee18ff8c161c904e36321ac70750acf7bc`.
- Disconnected failure archive focused tests: `7d922b135478ec918b32d250eccb467fc4b7642f` (17 authored parametrized cases).
- These 29 test cases are **authored**, not independently executed local pytest PASS.
  Exact-head GitHub CI must be checked separately; earlier Run533 GREEN does not
  certify this source/test head.

## 1. Local Memory update retention and time boundaries

`src/ark/memory/generation_fenced_cas.py` continues to use its opt-in
`BEGIN IMMEDIATE` transaction, exact retained event-prefix/row token and
revision predicate. Run534 adds:

1. Reject a persisted lifetime event sequence whose timestamp goes backwards,
   including across terminal-delete/recreation events.
2. After the in-transaction snapshot and the one caller-provided clock sample,
   reject `now < current.updated_at_ms`.
3. Reject a write at or after the **existing** row expiration boundary
   (`now >= expires_at_ms`), even with a previously observed valid token.
4. Reject a proposed newly expired row (`proposed_expires_at_ms <= now`).
5. Preserve exact v1 boundary of an equal-time non-expired update. Denials
   occur before changing the row or appending the event.

This is deliberately **not** a trusted-clock guarantee, a consent mechanism,
a permission to extend retention, or a replacement of frozen v1 `put/delete`.
The opt-in API still permits a caller to change/clear an *unexpired* record's
expiration; a future PermissionGate/retention policy must separately constrain
such intent before broader integration. A malicious independent SQL writer or
storage replacement is outside these local claims.

## 2. Hypothetical Planner failure persistence

`src/ark/agency/disconnected_batch_failure_archive.py` is a new create-only,
bounded local archive for `DisconnectedFailureFixtureReceipt`. It records
only deterministic request/plan/projection IDs, failed-step IDs, terminal
states, SHA-bound fixture digests, and a schema tag, not private mock inputs.
The file is written with exclusive creation and file fsync. Existing files
are never overwritten; partial/uncertain writes remain for manual inspection.

Read-only restart review requires an **independently retained** file SHA and
the *caller-provided* failure mask, recomputes the plan's deterministic
disconnected mock projection and successful fixture digests, compares exact
canonical bytes, and reads the file repeatedly with inode/size/mtime checks
against symlink/hardlink/race aliases. It returns only an inert witness with
separate `SUCCEEDED/FAILED/BLOCKED` counts and denied authority properties.

The failure mask is **hypothetical** and not derived as truth from the file.
A successful mock step is not a completed real action. Re-simulation is
bounded in-process fixture arithmetic, not a replay of an external WRITE.
File fsync alone does not authenticate writers or guarantee directory-entry
durability after a device crash. Real UNKNOWN WRITE outcomes stay manual-only.

## Focused adversarial test intent

- Expiration equality, just-before/just-after expiry, newly stale expiry,
  persisted event time regression and same-tick legacy compatibility.
- Failed/blocked dependency propagation across a three-step DAG, read-only
  recovery from fresh plan objects, negative-authority outcomes.
- Altered bytes/hash/mask, extra JSON fields, empty files, path aliases,
  file-replacement race, concurrent exclusive writers, failed fsync and
  final False authority-getter mutation.

## Integration / hard gates

No live microphone, external service, paid GPU/API, model load, Candidate,
protected V2 evaluation, protected contract mutation, automatic replay,
destructive erasure, new credential, approval, or main merge. PR #5 and #8
remain Draft/unmerged. Merge or live integration waits for exact-head GREEN,
independent permission/trusted-clock auditing, and separately explicit user
authorization wherever required.
