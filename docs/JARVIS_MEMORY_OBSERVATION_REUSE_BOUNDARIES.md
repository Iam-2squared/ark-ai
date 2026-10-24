# ARK JARVIS — Memory / Observation Recheck Boundaries

Status: **isolated, offline, reversible and zero-authority**. This record is
research evidence for Draft PR #8, not a frozen contract, release gate, V3 PASS,
protected FINAL result, authenticated approval, or permission to use data.

## One SQLite snapshot: scoped Memory events and current rows

`src/ark/memory/synthetic_multiscope_integrity_review.py` reviews 1–16
distinct namespaces of **one exact owner** using a single read-only Memory
SQLite transaction. It revalidates unchanged Memory v1 DDL and replays the
bounded local create/update/delete/expire event lifecycle. Event revisions and
current live Memory rows must agree for each selected namespace.

The returned metadata-only witness binds scoped event order, current memory
identity, source ID (inside a digest), current content hash, metadata hash,
revision and timestamps. No raw Memory content or source string is returned.
Global event IDs may have gaps from other namespaces. Untrusted caller-clock
timestamps are not assumed globally monotonic or authenticated.

These two retention modes serve DIFFERENT purposes:

- `retained_events` checks prior independently retained **event prefixes**,
  permitting later valid CAS updates or terminal events. Memory v1 event
  entries do not store past row-content hashes; event-prefix continuity alone
  CANNOT prove historical content or lawful deletion.
- `require_same_snapshot` checks an exact prior *current-row plus event*
  witness. Even a legitimate new CAS update is rejected until a new snapshot
  is reviewed; coherent same-revision row tampering is visible when an earlier
  receipt was genuinely preserved independently.

Local hashes are not cryptographic signatures or independent provenance.
A rewritten database plus rewritten local witness may still match. Memory
does not share an atomic transaction with revocation, Planner, authorization,
or external ToolBackend stores. A write after the final check can invalidate
a previously accepted receipt. Neither reuse, external disclosure, nor erasure
is authorized by any returned witness.

## Offline Observation reuse: original lineage and current freshness

`src/ark/observation_reuse_review.py` checks a previously cached local
`SyntheticObservationLineageWitness` twice: at its original check time to
re-bind the exact original age policy and parent/source identities, then at
the current supplied time to reject expired observations. Value-only cached
and envelope identity epochs are checked again after the final callback.

A changed age allowance or privacy scope does not silently relabel an old
receipt. Source/adapter IDs, SHA-256 values and clocks are caller-provided,
not hardware-origin proofs or consent attestations. The module contains no
camera, microphone, screen-capture, notification, or backend dispatch path.

## Recovery remains deny-only after SQLite restart

`tests/test_mock_cycle_restart_unknown_run382.py` exercises five synthetic
fault-injection boundaries across actual reopen of Planner Journal, durable
Occurrence, ActionAudit and audit-link SQLite stores. RUNNING remains UNKNOWN
after restart, irrespective of a new token/Occurrence; synthetic SUCCEEDED is
also not replayable. No actual ToolBackend effect is performed or proven.

## Gates that remain closed

Exact source/test HEAD and six Ubuntu/Windows Python 3.11–3.13 GitHub CI jobs
must be verified separately; a prior GREEN does not attest a newer SHA.
PROJECT_STATUS is the canonical latest checkpoint. Preserve frozen
V1/V2/Local UI/Launcher source and evidence, V3 PR #5 Draft/NOT_PASSED,
protected V2 FINAL, Candidate/weights, and all paid/external GPU gates.
Authenticated consent, issuer/subject/recipient/purpose, trusted clock,
independent witness custody, privacy/legal erasure decisions and backend
idempotency/effect reconciliation remain unresolved. UNKNOWN WRITE is never
automatically retried. No irreversible deletion, real tool dispatch, account
connection, physical-PC action or main merge is authorized.

## After bootstrap, SQLite WRITE entry points must not recreate lost evidence

The normal `SQLiteActionAudit.append` and `SQLiteMemoryStore.put/delete/purge_expired`
connection paths now use **existing-file** `mode=rw` SQLite URIs. Only
explicit `SQLiteActionAudit(...)` and `SQLiteMemoryStore(...)` bootstrap
may create a fresh database. A stale object's mutation against a missing
or moved initialized database fails before caller-clock sampling; it does
not create a plausible empty replacement. Literal `#` and `%` path
characters are handled via `Path.as_uri()` and the SQLite URI mode.

The audit append additionally pins its source path through a reentrant
clock hook and refuses reflected source retargeting before committing an
audit event. The separate coherent Memory snapshot reviewer likewise
pins its source path across clock sampling and row hydration; it will
not mislabel old SQLite rows as a newly substituted file.

These are **local filesystem safety guards**. They do not authenticate
file ownership, prevent a trusted caller from explicitly initializing a
new database, stop external file replacement at every possible instant,
or offer durable cross-store atomicity. An independent retained historical
witness is still necessary to detect coherent rollback. No personal-data
erasure, real tool execution or irreversible operation is performed by
these regression fixtures.

Focused tests: `test_action_audit_no_recreate_run382.py`,
`test_memory_mutator_no_recreate_run382.py`,
`test_memory_coherent_source_epoch_run382.py` and
`test_memory_multiscope_retained_shape_run382.py`. Exact GitHub
CI HEADs, run IDs and failure/success status belong to the canonical
project checkpoint; this document makes no unconditional GREEN claim.

