# JARVIS restart archive, ToolCall carrier, and Memory hydration boundaries — Run394

Status: **engineering/threat-model evidence; disconnected FREE-only Draft PR #8**.
Work basis: `d0c54f7a1491228051b81592bea6377bf8c5f4b8` (Run393 checkpoint).
No modification to frozen V1/V2/Local UI/Launcher contracts, historical V2 FINAL,
Memory v1 SQL DDL, or V3 PR #5. No inference of human authorization.

## A. Registered ToolCall carrier provenance

`ToolRegistry.resolve()` already rejected a changed `call.arguments` object
during its own lookup. Previously, `ToolRegistry.bind()` rechecked the
*value-derived* request ID afterward but not the **original mapping carrier**.
A callback between those phases could replace `arguments` with a different,
value-equal mapping. Both the request hash and bound action ID would remain
identical, concealing a changed caller-input epoch.

`bind()` now pins `original_arguments` **before** resolution and checks its
object identity at every existing binding boundary, including before return.
Focused fixtures inject new equal-valued mappings after `resolve()`, assert
rejection, and prove that no backend method runs. Hash/vector calculation and
stable bindings remain unchanged. Python-level carrier identity is not
authentication or cross-process isolation.

## B. Ordinary Memory v1 read lifecycle

Previously, `get()` could hydrate a verified SQLite row and then expose its
reflectively mutated `MemoryRecord` after a reentrant clock or expiry hook.
`search()` had clock-phase input checks but not a complete post-hydration
record/caller-input check across ranking and filtering callbacks.

New `_hydrated_record_epoch()` binds values, scope/metadata carriers, row ID,
content hash, revision, timestamps and metadata pairs. `get()` rechecks the
decoded row after clock/expiry; `search()` rechecks original query, Path
identity and decoded records after each read/hydration/filter/rank phase,
including empty results. Existing SQLite read snapshots and Memory v1 schema,
CAS, expiry semantics and event operations remain unchanged. Caller-injected
clock time remains **untrusted**. Returned plaintext remains local; no context
reuse, external disclosure or deletion is authorized by this change.

Existing tests required the historical fail-closed message
`(scope|query) changed during clock`. Intermediate CI #752/#753 rejected the
correct drift with a different diagnostic string. The original message was
restored without weakening the new checks. These exact commits **FAILED** and
are not called GREEN; the repaired source CI #754 is independently observed.

## C. Detached synthetic restart recovery archive

`synthetic_recovery_archive_review.py` adds a content-minimized, canonical
JSON witness from the already *read-only* `SyntheticRecoveryReview`. It binds
plan, occurrence, audit and optional occurrence-audit link witness values
alongside the step and registry-bound action identity, but **never serializes
raw ToolCall arguments, Memory text or execution tokens**.

An externally and independently retained archive can be supplied when the
SQLite handles are **reopened**. `recheck_synthetic_recovery_archive()`
validates canonical shape, explicit version, exact value types, a local
domain-separated SHA-256 checksum and retained per-store witnesses, then uses
`review_synthetic_write_recovery()` to reobserve independent stores.
The saved original archive bytes/digest are checked again after callbacks.
Append-only local history is permitted where existing witness rules allow it.
Truncated/contradictory local histories fail closed; this adds **no** cross-
database atomic transaction or OS-backed file identity.

**Threat ceiling:** A digest computed from the same local payload is NOT a
signature, trusted third-party anchor, authorized issuer or external receipt.
A party able to replace both the archive bytes and its checksum can forge a
different self-consistent archive. A matched archived audit/reservation and
even a locally `succeeded` Planner step NEVER establish external WRITE
success, replay eligibility or exactly-once delivery. UNKNOWN WRITE remains
UNKNOWN with automatic replay forbidden. The new API does not write an
archive to disk or invoke a ToolBackend; storage/custody is caller work.

## Evidence scope and continuing gates

- Relevant new regression fixtures:
  `tests/test_registry_bind_argument_identity_run394.py`,
  `tests/test_memory_read_hydration_epoch_run394.py`,
  `tests/test_synthetic_recovery_archive_run394.py`.
- No new GitHub Actions workflows were dispatched manually; existing public
  repository pull-request CI is the only cloud validation.
- A new commit's CI is **not inherited** from its parent, and a local synthetic
  archive is not an independent authenticated source. See the latest
  `docs/PROJECT_STATUS.md` for exact-HEAD job results at checkpoint time.
- Blocked: real ToolBackend dispatch, live camera/microphone, actual consent
  or secrets, real training or Candidate weights, paid/external compute,
  protected V2 FINAL opening, Candidate promotion, destructive erasure,
  frozen-contract changes, and approval-gated main merge.
- Next: independently retained crash-boundary evidence for genuinely
  disconnected Planner/Claim/Occurrence/Audit workflows; exact local
  Memory/Personal Context privacy retention/revocation constraints; mock
  Observation/Startup/Scheduler; V3 free-only identity/path gate reviews.

**Integration disposition:** these are reversible offline foundations.
No additional live-execution permission is conferred; complete JARVIS
remains NOT_PASSED.
