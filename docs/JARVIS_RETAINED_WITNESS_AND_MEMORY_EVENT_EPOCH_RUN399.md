# Run399 — Retained-evidence ingress and Memory event-row epoch fences

**Status:** engineering threat model / implementation evidence pointers only.
CI conclusions belong to the exact GitHub commit and must be read separately;
this document does not declare any test or roadmap gate passed.

**Scope:** additive, reversible JARVIS safety research on Draft PR #8.
No V1/V2/Local UI/Launcher/V3 frozen contract or Memory v1 DDL change.
All examples are disconnected, locally generated fixtures.

## Package A — revocation witness custody before callbacks

Files:
- `src/ark/personal_context_revocation_continuity_review.py`
- `tests/test_revocation_early_carrier_epoch_run399.py`

**Previous gap:** `review_revocation_continuity` called a potentially
reentrant retained-witness integrity method before taking its first historical
epoch snapshot. A reflected in-place replacement could change which prior
history was accepted; end-only value equality also failed to detect
value-equal tuple replacement.

**Fence:** capture the original retained `rows` carrier, each row carrier
and `witness_id` before *source* and retained-shape callbacks. Check the
original source path and exact retained carriers before/after integrity
validation, every committed-row observation and the final retained-prefix
comparison. Malformed input remains denied. No veto marker is removed,
consent inferred or erasure requested.

**Failure matrix:** first source validation, first retained integrity,
SQLite schema validation and later retained integrity; for each, replace the
outer history tuple or an inner row carrier by an equal-valued clone.
Eight parametrized regressions require denial, followed by successful
read-only verification when the caller restores its actual original carrier.

## Package B — claim/reservation witness custody before callbacks

Files:
- `src/ark/agency/synthetic_claim_occurrence_recheck_review.py`
- `tests/test_claim_source_early_witness_epoch_run399.py`

**Previous gap:** the detached claim-link and reservation evidence was
first validated and *then* pinned. During a reentrant `assert_shape()`
or `assert_integrity()`, it could be reflected into a different valid
historical epoch. A value-equal reservation `row_hashes` tuple swap did
not change the legacy value comparison.

**Fence:** capture exact validated-type retained values and the identity
of the reservation row tuple *before* invoking shape or integrity
callbacks. Inspect the pinned link source and both retained witnesses
after these callbacks, after sidecar/ledger reads, after continuity
validation and after final source reads. The previously accepted
unchanged-history diagnostic remains read-only and non-authorizing.

**Failure matrix:** link-witness shape validation, reservation integrity,
source continuity review and link-witness read. Four regressions require
denial at the first affected phase and verify an unchanged local history
after original evidence is restored. A claim↔occurrence match remains
unauthenticated and does NOT prove external effects or approval.

## Package C — per-row ordinary Memory event-read ingress

Files:
- `src/ark/memory/sqlite_store.py`
- `tests/test_memory_event_row_epoch_run399.py`

**Previous gap:** `SQLiteMemoryStore.events` checked the scope and
database-path epoch after its entire event hydration loop. A synthetic
reentrant decoder for event #1 could retarget caller scope or Path, and a
later decoder could restore it before the final check.

**Fence:** validate scope and exact Path carrier after read-transaction
schema validation, after SELECT, before and during each event decode,
immediately following event identity and scope normalization, and after
constructing every immutable event. Preserve frozen Memory v1 schema and
the event-ID (not clock timestamp) ordering contract. No new event,
erasure, permission or data-export path is introduced.

**Failure matrix:** reflected Path and scope drift during event-ID
validation or event construction (four regressions), each requiring
denial before processing the second event. Restoring the original
fixture scope/source permits the two saved content-free events to be
read again.

## Claim limitations and non-proofs

These are **in-process observation-epoch guards**, NOT kernel inode/file
descriptor custody, authenticated storage provenance, nonrepudiable
human consent, a trusted clock, atomic cross-SQLite snapshot or an
exactly-once external action. An adversary who rewrites an offline SQLite
file and its unauthenticated local digest may still forge apparent history.
Checks cannot eliminate races immediately after the final observation.

The tests do not grant actual ToolBackend execution, network delivery,
operating-system permissions, notifications, camera/microphone access,
personal data deletion, protected V2 evaluation, paid V3 training or
Candidate promotion. UNKNOWN WRITE remains UNKNOWN and non-replayable.

## Validation protocol / next independent work

1. Link each source/test package and any intermediate failure to its
   **exact commit SHA** and inspect six platform/Python jobs; no ancestor
   success is inherited.
2. Diagnose new failures without weakening deny conditions, via ordinary
   GitHub Contents writes. Never force-update a ref or bypass a rejected
   source/test write.
3. Continue Planner/PermissionGate/Occurrence/ActionAudit recovery
   integration only after lower-layer evidence is GREEN, and keep
   dispatch disconnected.
4. Audit Memory search/snapshot and revocation privacy-use boundaries;
   preserve memory DDL, frozen experiment/evaluation labels and PR #5
   Draft/NOT_PASSED gates.
