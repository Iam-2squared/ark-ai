# JARVIS Reentrant Evidence-Epoch Review — Run 387

Status: **offline safety workstream / deny-only / NOT production authorization**.
Branch: `research/jarvis-foundations` (Draft PR #8), based on the Run 386
checkpoint `ab129dbce951d69cee591a42a519a44be4995e40`.
This is a threat-model and regression-evidence map, not a PASS certificate.

## Threat being closed

Four otherwise independent diagnostic paths had narrow callback/TOCTOU
windows in which an immutable-looking Python carrier could be replaced by
reflection. A frozen dataclass does not prevent `object.__setattr__`; nor
does comparing two `Path` values detect an equal-string replacement.
The local safety rule is that a diagnostic MUST NOT silently reinterpret
a different *initial* action, token, Memory source or Trigger source as the
same evidence epoch merely because the final values compare equal.

### 1. Registry-bound PermissionGate (first bind)

`src/ark/agency/policy.py` now pins the ToolCall identity, exact
arguments object, and optional OneShotAuthorization fields **before the
first registry callback**. These fields are checked after each bind, after
materializing grants, and around the pre-spend registry check. This matters
because two registry.bind() calls can agree on an already-substituted scope or
token. Tests: `tests/test_registered_permission_first_bind_epoch_run387.py`.
A process-local consumed-token set is *not* restart-safe authenticated
approval, cannot certify issuer/subject consent, and never dispatches tools.

### 2. ActionAudit SQLite source custody

`src/ark/agency/audit.py` now checks initialized Path *object identity*
at write connection admission, before append commit, during read-only
evidence review, and after event hydration, including empty results. A
speculative INSERT is rolled back if the source is swapped before commit.
Tests: `tests/test_action_audit_source_epoch_run387.py`.
These guards cannot detect OS-level same-path file replacement, concurrent
post-return tampering, or forge-proof provenance.

### 3. Privacy retention inventory cross-store inputs

`src/ark/personal_context_retention_review.py` now pins both the SQLite
Memory source and the independent revocation journal source *before* the
first revocation review. Path identity is checked around the Memory read,
before commit, and after the second revocation review. No content is returned
in the diagnostic receipt and no data is deleted.
Tests: `tests/test_retention_source_epoch_run387.py`.
Two SQLite databases are not one serializable transaction; a simultaneous
write or revocation may occur immediately after these checks.

### 4. Observation-to-Proactive Trigger handoff

`src/ark/proactive_observation_lineage_fence_review.py` now pins the
Trigger ledger source object across *both* lineage and freshness passes.
Previously each freshness pass protected its own internal snapshot, but an
equal-value Path replacement *between* passes was not detectable using
ordinary Path equality in the outer reviewer.
Tests: `tests/test_observation_trigger_source_epoch_run387.py`.
Content hashes and prepared triggers do not authenticate cameras, users,
physical sensors, clocks, notification permissions, or side effects.

## Regression expectations and fail-closed limitations

All regression fixtures use synthetic identifiers and temporary SQLite files.
They exercise both unchanged normal behavior and reflected input/source
changes during reentrant callback boundaries. No tests intentionally perform
physical computer actions, media acquisition, external notifications,
training, protected final evaluation or real ToolBackend execution.

Exact GitHub SHA-specific CI evidence must be read from the corresponding
workflow run. GREEN on one commit cannot be assigned to later source,
test, documentation or checkpoint commits. A temporary Windows HTTP
test failure outside these modules is not an authorization bypass; it
must be investigated as a separate CI reliability issue if observed.

These guards do **not** establish authenticated consent, trusted time,
atomic cross-store snapshots, durable exactly-once real-world actions,
legal deletion authority, genuine provenance signatures, or irreversible
architecture approval. In particular an UNKNOWN external WRITE never
becomes safe to retry through any of these diagnostic receipts.

Frozen V1/V2/Local UI/Launcher contracts, V3 PR #5 Draft/NOT_PASSED,
protected V2 FINAL, and the zero-cost/no-new-paid-services restriction
are unchanged.
