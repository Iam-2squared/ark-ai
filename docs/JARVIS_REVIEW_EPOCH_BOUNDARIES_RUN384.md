# ARK JARVIS synthetic read-side epochs — Run 384

Status: disconnected research-only evidence. No runtime integration, protected evaluation, or dispatch permission.

## Scope and threat model

The offline reviewers consume frozen dataclasses, caller-supplied timestamps, local SQLite stores and optional **independently held** prior witnesses. `frozen=True` is not a security boundary: `object.__setattr__` can replace individual fields while a reviewer is inside a reentrant callback. A *different but self-consistent* retained witness can make a locally rewritten history appear continuous. A saved `Path` may also be rebound to another SQLite database during a review.

This document records three narrow, fail-closed fixes. They do **not** authenticate user consent, the issuer, privacy scope, a trusted clock, an external effect, or the identity of a physical database file.

## Implemented controls

### Personal Context reuse

`personal_context_reuse_review.py` pins the original snapshot request fields (owner, namespaces, query, per-scope limit, include-expired option), selection policy values (limits and revision), cached nested values, and the Memory/revocation source `Path` object identities. The reviewer compares them after the fresh Memory + revocation check. It does not accept a fresh projection computed with silently rebound selection intent. The result remains a content-free diagnostic; `context_use_authorized`, `external_disclosure_authorized`, and `dispatch_authorized` are always false.

Fixture: `test_personal_context_reuse_policy_epoch_run384.py` verifies reflected request/policy/source changes after projection and an unaffected success path.

### Memory event history continuity

`memory/synthetic_event_continuity_review.py` now snapshots scalar values of an optional independently retained history witness before SQLite event replay/row hydration. It rejects a witness re-bound to a different *valid* event prefix during a reentrant row conversion. The Memory `Path` must remain the original object identity, not merely an equal pathname. This remains a read-only check of existing frozen Memory v1 events and live rows.

Fixture: `test_memory_event_witness_epoch_run384.py` checks substituted valid newer/older retained prefixes, equal-value source rebind, and unchanged behavior.

### Claim / occurrence provenance

`agency/synthetic_claim_occurrence_recheck_review.py` pins the link-sidecar source `Path` object and exact scalar values for retained link/reservation witnesses and the first observed witnesses. It refuses provenance reviews that silently switch to another, internally valid sidecar or replace a retained witness with an earlier history during reads. It continues to compare before/after reservation ledgers without claiming an atomic transaction.

Fixture: `test_synthetic_claim_recheck_epoch_run384.py` checks link-store source substitution, retained link/reservation substitution and unaffected offline review.

## Boundaries and remaining gaps

- **Not full integrity:** changes that occur and are perfectly restored between two observations cannot be detected by these equality checks. Reflective mutation after the final read is also not prevented by a returned receipt.
- **Not OS file identity:** pinning Python `Path` references does not detect atomic replacement of a file at the same pathname, WAL attacks, or filesystem compromise. Independently protected evidence/keys and trusted platform identity remain unresolved.
- **Not an atomic snapshot:** Memory itself uses local SQLite transactions, but the claim/revocation/Occurrence/Audit stores are separate databases without a global commit or consistency protocol.
- **Not consent, authority or proof of effect:** local SHA digests and synthetic claim fields cannot authenticate a human issuer, subject, recipient, or intended use. A persisted synthetic SUCCEEDED or checked linkage cannot establish the external outcome of a WRITE.
- **No runtime permission changes:** UNKNOWN WRITE must never be automatically replayed; no real backend, GPU training, paid service, user-secret collection, media capture, or notification is enabled.

All modifications are isolated under Draft PR #8. Existing V1/V2/Local UI/Launcher and V3 Contract 1 gates are unchanged; V3 PR #5 remains Draft/NOT_PASSED. CI results must be associated with their exact HEAD and recorded separately in the canonical PROJECT_STATUS checkpoint.
