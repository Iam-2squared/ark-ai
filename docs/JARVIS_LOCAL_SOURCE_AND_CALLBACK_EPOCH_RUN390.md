# Run390 — Local SQLite source and disconnected callback-epoch defenses

This is **technical evidence and threat-model documentation**, not a JARVIS
readiness certificate. Changes are confined to isolated, mock/synthetic
foundations on Draft PR #8. Frozen V1/V2/Local UI/Launcher contracts, DDL and
evaluation evidence remain outside this change.

## 1. SQLite Memory source epoch — `sqlite_store.py`

The source-epoch of an existing `SQLiteMemoryStore` is now pinned across
`put`, `search`, `delete` and `purge_expired`. A reflected reassignment
of the Python `Path` object (even to a different object representing the
same pathname) is rejected after injectable read/clock/event callbacks.
Writes fail before transaction commit and roll back uncommitted rows/events.
The search and expiry zero-row cases are checked as well.

`tests/test_memory_transaction_source_epoch_run390.py` exercises ordinary
CAS update/delete, source drift during the clock, source drift after an
appended event, rollback/no ghost audit event, empty search, and zero-row
expiry. No Memory v1 schema migration or personal-data transfer is involved.

This only verifies Python object epoch identity. It is **not** kernel inode
custody, filesystem access control, signed historical provenance, rollback
resistance, or a guarantee against a path swap that happens entirely between
checks. The SQLite transaction guarantees apply only inside one database.

## 2. Claim ↔ Occurrence ↔ Planner provenance phase fences

`synthetic_claim_recovery_provenance_review.py` originally compared
important local inputs after four disconnected reads. A reflected argument,
topology or source may change transiently between callbacks and be restored
before that final comparison. The new guard retains initial envelope fields,
ToolCall, Registry revision, Planner topology carrier, Path objects and
independently retained witness fields. It checks these **after each** recovery
or association-read callback, before the next callback begins.

`tests/test_claim_provenance_cross_phase_epoch_run390.py` includes
adversarial callbacks where a later read would restore a transient
same-path-object/topology/argument substitution. The first phase must reject
before the restoration callback. The result remains deny-only even when all
local records agree.

Historical witness digests are locally computed, **not signatures**.
Claim binding does not verify a human issuer, subject or recipient, nor
authorize a real backend WRITE. The four reads across separate SQLite files
are not one global atomic snapshot. UNKNOWN external effects remain UNKNOWN;
automatic retries are forbidden.

## 3. Observation ↔ proactive Trigger per-phase input pinning

`proactive_observation_lineage_fence_review.py` now verifies the original
envelope metadata, selected observation, trigger receipt, policy and any
retained trigger witness after **each** of two lineage and two trigger
freshness observations. This closes transient reflected changes that a
final-only input comparison could miss between independent callbacks.

`tests/test_observation_cross_phase_input_epoch_run390.py` exercises
source/policy/receipt reflection after the first lineage pass, retained
witness mutation after trigger freshness, and the stable diagnostic-only
path. It grants **no** actual media capture, notification, disclosure or
ToolBackend dispatch.

## Invariants and continued constraints

- No paid compute, external APIs/GPU, credentials, account connections,
  purchases, private-data deletion/export, training, Candidate artifacts or
  V2 protected-final evaluation are invoked by these reviews.
- A Python Path identity check does not defend against external filesystem
  replacement, ABA after a return, process compromise or OS-level tampering.
- Clock arguments are untrusted; hashes alone do not authenticate consent,
  reviewer decisions or real-world execution effects.
- No cross-SQLite atomic transaction, durable external idempotency receipt or
  trusted-clock audit-before-action proof is added here.
- PR #8 stays Draft/unmerged. V3 PR #5 stays Draft/NOT_PASSED.
  Frozen contracts remain untouched. There is no main merge.

## Validation protocol

For each changed exact HEAD: use the already configured public PR-triggered
GitHub Actions matrix (Ubuntu/Windows, Python 3.11–3.13). Report its actual
run ID and job statuses separately in `docs/PROJECT_STATUS.md`. Earlier
GREEN evidence cannot be inherited by later source/test/document commits.
If the new tests expose a failure, repair that precise defect by the ordinary
GitHub Contents API and preserve the failure in the checkpoint. Do not
dispatch a duplicate equivalent workflow run.

## Next integration gates

1. Finish exact-head all-matrix validation and identify any regressions.
2. Keep Planner/Registry/Claim/Occurrence/ActionAudit cross-store recovery
   deny-only until authenticated consent, trusted time and real external
   idempotency evidence exist.
3. Strengthen Memory CAS/TTL/coherent-snapshot witnesses and privacy-safe
   Personal Context retention/veto without opening real-world action lanes.
4. Extend disconnected Scheduler/Observation startup probes while preserving
   no-capture/no-notification constraints.
