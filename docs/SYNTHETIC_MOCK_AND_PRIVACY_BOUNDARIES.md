# Offline mock-action and privacy revocation fault matrix

**Scope:** research-only Draft PR #8, `research/jarvis-foundations`. These
modules and tests exercise disconnected local SQLite fixtures only. They do
**not** authorize, execute, notify, export, monitor a real person, validate a
human issuer, open frozen evaluations, or alter existing v1/v2 contracts.
All hashes and clocks are local/caller-supplied unless explicitly stated.

## Durable proactive trigger identity

`proactive_synthetic_review.py` verifies that every stored
`trigger_<sha256>` primary key recomputes from its persisted scope, policy,
source and observation digests. A syntactically valid but independently
rewritten digest or primary key now fails closed during opening, counting or
another preparation.

This local consistency gate does **not** detect a coordinated, fully
recomputed rewrite of the entire fixture. It cannot authenticate policy,
source material, observations, consent or monotonic physical time.
`tests/test_proactive_trigger_binding_run373.py` covers individually rewritten
canonical digests, primary-key replacement, restart and deduplication **after**
the minimum-interval gate.

## Synthetic mock-action crash boundaries

`agency/synthetic_mock_action_cycle_review.py` is a **fixture coordinator**,
not an executor. No registered backend is ever invoked.

| Boundary | Durable state at an injected stop | Interpretation |
| --- | --- | --- |
| Before startup preflight passes | No new fixture state | Denied |
| After journal `RUNNING` | Plan RUNNING; no new occurrence | UNKNOWN, no replay |
| After SQLite occurrence reservation | Plan RUNNING; occurrence persisted | UNKNOWN, no replay |
| After pre-action audit append | Plan RUNNING; occurrence plus audit | UNKNOWN, no replay |
| After optional audit-sidecar link | Plan RUNNING; occurrence, audit and a local link | UNKNOWN, no replay |
| After pure in-memory mock marker | Same durable state as above | UNKNOWN, no replay |
| After synthetic `SUCCEEDED` journal | All three stores updated separately | Synthetic success only; real outcome unknown |

Even the complete path records no external side effect. Any restart or
retry attempt with a non-PENDING step is rejected; a different occurrence ID
cannot make an ambiguous WRITE safe to repeat. The test backend throws if its
`execute` method is ever called. `tests/test_synthetic_mock_action_cycle_run373.py`
covers the above crash points, invalid input, token expiry and registry
WRITE/READ downgrade. **There is no cross-store atomic transaction** and no
audited authenticated occurrence field in frozen ActionAudit v1.

The optional new `link_store` argument allows the mock cycle to commit a
**fourth, independent** SQLite audit-link event *after* the pre-action audit
and *before* the pure mock marker. Injected `after_audit_link` stops leave
RUNNING and cannot be retried. Passing an invalid sidecar or requesting this
fault without a sidecar fails before journal mutation. A missing or malformed
sidecar discovered after the audit must leave UNKNOWN, not mock success.
This optional link does not supply proof of the underlying external action.
`tests/test_synthetic_mock_sidecar_cycle_run374.py` covers these paths.

## Privacy-safe revocation veto (not consent)

`personal_context_revocation_review.py` adds an independent,
content-minimized SQLite revocation ledger. It records only domain-separated
owner+namespace hashes and a caller-supplied revocation timestamp. A scope
may be vetoed once, with no local regrant API. The read-through helper obtains
a **new coherent Memory snapshot on every request**, bracketing its projection
with pre/post read-only revocation checks. It refuses a revoked scope, expired
record inclusion, duplicate scopes and malformed persisted schema/rows.
No plaintext owner, namespace or Memory content is stored in the veto ledger.

**No consent is inferred from an absent veto.** The veto can be created or
cleared by an untrusted local actor; nothing authenticates a subject, issuer,
recipient or lawful purpose. Two SQLite stores cannot be snapshotted
atomically: revocation between the final check and consumption remains
possible. The wrapper returns ephemeral informational data **only**, not a
permission to feed a model, execute a tool, transmit a notification or export
personal data. Revocation markers do not themselves erase existing Memory,
logs, backups or prior bundles.

`tests/test_personal_context_revocation_run373.py` checks fresh Memory
revisions, restart persistence, isolation by namespace, mid-read revocation,
invalid clocks, schema/row corruption and missing-file refusal. Test input
contains synthetic fixture text only.

## Independently retained revocation evidence

`personal_context_revocation_continuity_review.py` produces an ordered
content-free witness of persisted veto rows. Passing a **genuinely earlier,
separately preserved** witness detects missing or changed revocations,
while allowing new veto markers. It rechecks retained witness integrity in
the same read transaction; malformed or reflectedly changed evidence fails
closed. Deleting and reconstructing the SQLite file does not silently satisfy
a separately retained witness.

A locally regenerated witness from an already tampered database provides no
protection. There is no external root of trust, signed receipt, trusted
filesystem, automatic key management, verified erasure or authenticated
consent. `tests/test_personal_context_revocation_continuity_run373.py`
checks append, deletion, rewrite, forged witness and missing-file paths.

## Opt-in retained-history fence on fresh projection

The fresh, veto-bracketed Personal Context wrapper now also reads an
independent revocation-history witness at the beginning and rechecks that
prefix after the Memory snapshot and projection. An optional
`retained_revocations` argument may be an **earlier, separately retained**
`SyntheticRevocationWitness`; a false type or corrupted witness is rejected.
This detects coordinated deletion of any previously witnessed veto, including
one for an unrelated namespace, when it happens during a context review.

When the caller supplies no earlier witness, the initial local witness is
still useful for detecting changes **during that one call**, but it cannot
recover revocations already removed before the call. A later edit, deletion
or external data use can race after the final read. Tests in
`tests/test_personal_context_retained_fence_run373.py` cover retained veto
deletion before a review, deletion during the Memory clock hook, unrelated new
veto markers, and malformed retained carriers. There is still no externally
authenticated subject/issuer, real consent, cross-store transaction, or
permission to provide the resulting content to a live model or recipient.

## Synthetic occurrence-to-audit link sidecar (research only)

`agency/synthetic_occurrence_audit_link_review.py` creates a **separate**
append-only SQLite fixture: one canonical occurrence ID, registry revision,
bound action ID and request ID, paired with one existing ActionAudit v1
pre-action event ID and its complete canonical event digest. It does not
change the preexisting ActionAudit v1 schema. Its write preflight checks the
registry-bound WRITE identity, verifies the occurrence against a read-only
snapshot of the durable reservation ledger and the pre-action event against
the actual ActionAudit row, and then commits a local hash-chained link.

Only `synthetic_audit_before_mock` events qualify. Duplicate occurrence
links and duplicate event IDs are rejected by SQLite uniqueness constraints.
Schema drift, invalid row identities, non-monotonic locally supplied link
times, direct row rewriting and malformed historical chains fail closed.
An *independently retained* prior `SyntheticAuditLinkWitness` detects
deletion of a known prefix; a re-created local witness cannot certify a
missing history. The sidecar refuses to regenerate missing DB files when
reading or appending. Corresponding synthetic regression tests are in
`tests/test_synthetic_occurrence_audit_link_run374.py`.

**Critical:** the three source/read/write SQLite transactions are not
atomic together. A link is a point-in-time local consistency diagnosis, NOT
an authenticated issuer approval, signed external witness, source-ledger
tamper protection, proof of effect, production Exactly-Once or permission to
execute. There is no backend call. Subsequent mutation of an external
ledger must be separately re-reviewed with a trusted independent witness.
The mock cycle must not use a link to auto-replay UNKNOWN WRITE.

## Independently retained proactive trigger history

`proactive_synthetic_continuity_review.py` gives a read-only,
content-minimized witness over all canonical persisted trigger rows, including
bound digests and observed/prepared timestamps. A later snapshot can append
new preparations without invalidating a genuinely earlier witness, while
deletion or a coordinated internally valid rewrite of an earlier trigger
requires rejection. Invalid witness carriers and changed SQLite schemas
are refused; a missing fixture file is never recreated during review.

`tests/test_proactive_synthetic_continuity_run374.py` exercises normal
append, persisted-row removal, coordinated recomputation of a trigger
primary key, witness tampering, missing-file refusal and schema drift.

The proactive fixture's `prepare(..., retained=...)` now optionally
validates an independently retained prior `SyntheticTriggerWitness` **inside
its SQLite BEGIN IMMEDIATE admission transaction**, before any new trigger
is inserted. This closes the separate-read/admission race for the *local
proactive database*, but not the absence of external witness authenticity.
A missing/rewritten historical row rejects the attempted new preparation;
valid append-only history leaves the existing cooldown, rolling budget and
duplicate fences unchanged. Existing callers without a retained witness
remain supported but cannot detect a previously removed trigger.
`tests/test_proactive_retained_admission_run374.py` tests valid append,
deletion, timestamp rewrite, bad witnesses and preserved budgets.

Hashes of low-entropy scope/policy identifiers can still be guessed.
An attacker controlling the SQLite file and all witness copies can forge a
new consistent history. No policy authentication, real observation,
notification authorization, external clock, consent or user identity exists.

## Release and integration gates

These fixtures must remain disconnected until exact-head CI is GREEN and
independent security/privacy review establishes: authenticated issuer and
revocation rights; durable approval scope/purpose/recipient binding; trusted
clock; atomic or explicitly recoverable occurrence/audit/journal invariants;
external backend idempotency and UNKNOWN reconciliation; privacy erasure and
retention lifecycle; launch readiness; and user-approved side-effect enabling.

Do not turn any of the local receipt flags into external execution authority.
The existing protected V1/V2/Local UI/Launcher evaluations and V3 PR #5
Draft/NOT_PASSED gates remain unchanged. No paid services or compute are
required or invoked by these fixture reviews.
