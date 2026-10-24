# ARK disconnected replay and privacy veto phase-boundary review — Run393

**Status:** FREE-only synthetic implementation and regression evidence. This
document records local fail-closed behavior, not real user permission, a
multi-database transaction, trusted time, media access, a production tool
executor, external exactly-once delivery, protected V2 evaluation, or JARVIS PASS.

## Threat model: transient mutations between independent reads

A frozen Python dataclass can still be reflectively rewritten with
`object.__setattr__`. Likewise, a mutable store field holding a `Path` may
be replaced by an equal-value but distinct object while a callback runs.
A reviewer that checks an input only at the end may miss an earlier
mutation when a later callback restores it. These checks cover **observed
synchronous phase boundaries**, not arbitrary privileged code or OS inode swaps.

### Package 1 — Memory event continuity

`src/ark/memory/synthetic_event_continuity_review.py` now captures its
original scope, source Path **object**, and independently retained witness
fields, and rejects drift after schema work, SQLite event fetch, **each**
event digest replay, live-row fetch and **each** live-record hydration.
The final check remains. Regression file:
`tests/test_memory_event_phased_epoch_run393.py` (**8** cases).

A successful result means only that the local Memory v1 event lifecycle,
live-row revisions and supplied historical-prefix witness reconciled
under the read transaction and observed input epochs. Event hashes do not
authenticate past content or grant reuse/deletion/export. The Memory v1
schema, event semantics, CAS rules and expiry behavior were not modified.

### Package 2 — Cross-store WRITE recovery

`src/ark/agency/synthetic_recovery_triage.py` now rejects reflected
action/source/retained-witness drift **immediately** after the reservation
snapshot and each independent final Planner, reservation and ActionAudit
recheck. The optional occurrence-audit sidecar also checks input epochs
after its local link replay, query and audit-event reads. Regression file:
`tests/test_recovery_cross_store_phase_epoch_run393.py` (**8** cases).

All three/four SQLite stores remain independent: there is **no**
cross-store atomic snapshot or external backend reconciliation. A
`RUNNING` WRITE recovered as `UNKNOWN` stays ambiguous and **MUST NEVER**
be automatically retried. An audit receipt or reservation record is not a
real side-effect acknowledgement. PermissionGate, ToolRegistry and claimed
approvals do not constitute authenticated human consent.

### Package 3 — Personal Context revocation continuity

`src/ark/personal_context_revocation_continuity_review.py` now checks
source Path identity and retained history values directly after
SQLite schema validation, revocation-row query, local witness hash,
witness-integrity replay, and before/after the read transaction commit.
This prevents a later hash callback from hiding an observed earlier
source/evidence substitution. Regression file:
`tests/test_privacy_revocation_phase_epoch_run393.py` (**6** cases).

A missing veto is **not** affirmative consent. This check neither
deletes personal data nor proves forensic erasure, prevents later
revocation races, or authorizes inference, disclosure, notifications or
model/tool use.

## Verification and stop conditions

The three work packages add **22** focused regression parameterizations
(8 + 8 + 6). CI outcomes must be reported for their **exact GitHub
commit SHAs**; earlier successful runs do not transfer to a subsequent
source, test, document or checkpoint commit. A test in a free, synthetic
fixture is not protected V2 FINAL and does not demonstrate production
exactly-once external writes.

Do not dispatch live backends, start external/paid GPU or API usage,
generate a real Candidate or model weights, open frozen evaluations,
change Memory v1 / V1 / V2 / Local UI / Launcher contracts, add credentials,
perform irreversible privacy operations, merge into main or promote V3.
PR #8 remains Draft and PR #5 remains Draft/unmerged/NOT_PASSED.

## Next plan / 今後の方針

1. Verify all Ubuntu/Windows Python 3.11–3.13 jobs on each exact final
   source/test head and checkpoint. Correct actual regressions through
   ordinary GitHub Contents writes, preserving fail-closed semantics.
2. Create **independent** cross-store crash/restart fixtures checking
   Planner UNKNOWN, authorization-claim correlation, reservations, audit
   and sidecar history. Never upgrade synthetic matching to a real WRITE
   completion or replay permission.
3. Advance privacy-safe retention/revocation and Memory CAS/expiry/
   coherent snapshots; retain witnesses independently of mutable SQLite.
4. Leave real dispatch blocked until trusted clock and authenticated issuer,
   OS-backed source custody and backend idempotency/reconciliation are
   established and explicitly authorized.
