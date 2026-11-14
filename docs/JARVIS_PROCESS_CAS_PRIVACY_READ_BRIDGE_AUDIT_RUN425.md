# ARK AI — Run425 disconnected process-race and audit custody evidence

**Scope:** `research/jarvis-foundations` / Draft PR #8. This is an engineering
fixture and CI record, **not** human approval, signed time, protected V2
evaluation, real WRITE execution, or an externally enforceable exactly-once
guarantee.

**Invocation work-basis HEAD:** `63ee79c04461b3c8412043bf3eb1eb764f74675e`
(Run424 checkpoint, independently verified as all-six SUCCESS on CI #1155 /
40196267344 before these packages). V3 PR #5 remains Draft / NOT_PASSED,
and frozen contracts, Memory v1 and ActionAudit v1 DDL are unchanged.

## New reversible work packages

1. **Memory expiry/delete-versus-refresh CAS under two *independent Python
   processes*.** `tests/test_memory_cross_process_expiry_delete_race_run425.py`
   at `e6186d358811fe3e363b2b7174d0d65f1c55c5d1`. Four parameterized
   cases race a revision-1 UPDATE against expiry purge or revision-1 deletion,
   twice each. The SQLite writer lock permits exactly one logical effect:
   (a) successful revision-2 update with one `update` audit row and no
   physical erasure, or (b) one `expire`/`delete` event and no remaining
   row. A stale competing operation is rejected and cannot create a second
   contradictory audit entry.
2. **READ-bridge Planner quarantine.**
   `tests/test_recovery_read_bridge_reserved_descendants_run425.py`
   at `84d1a7266083600af766d19fe41f79fcafe2405a`.
   Three cases distinguish RUNNING/UNKNOWN WRITE, reserved descendant PENDING
   WRITE, and terminally FAILED WRITE across an intermediate READ dependency.
   Independent branches stay separate; downstream WRITEs are held/blocked
   rather than replayed or declared externally resolved.
3. **Cross-process privacy revocation single-winner.**
   `tests/test_privacy_revocation_cross_process_run425.py`
   at `ae50d0abc8122be80430c1e263a85b490bf82c23`.
   Two independently initialized local processes race to persist the *same*
   scope veto. Exactly one durable digest/timestamp row must win, and the
   other process must receive the explicit already-revoked diagnostic.
   Read-only post-restart lookup still denies use. No plaintext scope is
   written into the veto ledger; no actual erasure or consent is inferred.
4. **Cross-process content-minimized ActionAudit writes.**
   `tests/test_action_audit_cross_process_append_run425.py`
   at `0ecee382065a2f747913f60122af6b40b4ee7bba`.
   Two independent local processes append separate pre-action audit rows,
   validate unique ordered SQLite IDs and identities, and confirm a
   controlled mock argument marker is absent from raw SQLite data.
   Append is explicitly NOT a backend action, signed receipt or permission.
5. **Pre-/post-COMMIT original ActionAudit subject and returned-event custody.**
   `src/ark/agency/audit.py` at `c241bfa18264ac76f9faaee8dce00d0ebb3da356`.
   This additive fail-closed fence checks exact original ToolCall carrier
   identities after the injected clock and INSERT callbacks, checks them
   again after COMMIT, and refuses a returned event whose constructed field
   carriers differ from the exact persisted inputs. **An error after COMMIT
   does not undo the audit event or authorize a blind replay.** Original v1
   SQL schema, normal event fields and legacy caller API remain unchanged.

## CI and verification facts at this evidence creation

- **#1155 / 40196267344:** Run424 opening checkpoint, all six SUCCESS.
- **#1156 / 40196997159:** Memory process races, all six SUCCESS; Ubuntu
  Python 3.13 Ruff PASS, `2681 passed / 1 skipped`.
- **#1157 / 40197271039:** READ-bridge recovery, all six SUCCESS; Ubuntu
  Python 3.13 Ruff PASS, `2684 passed / 1 skipped`.
- **#1158 / 40197427416:** Revocation process races, all six SUCCESS; Ubuntu
  Python 3.13 Ruff PASS, `2686 passed / 1 skipped`.
- **#1159 / 40197508253:** ActionAudit process races, all six SUCCESS; Ubuntu
  Python 3.13 Ruff PASS, `2688 passed / 1 skipped`.
- The subsequent ActionAudit source fence at
  `c241bfa18264ac76f9faaee8dce00d0ebb3da356` is not covered by those
  earlier exact-HEAD GREEN results. Its new CI, focused constructor
  regressions and any later checkpoint HEAD must be verified **independently**
  before any PASS statement. Do not extrapolate CI from its parent commit.

## Boundaries / unfinished work

Every test uses disposable local SQLite and stdlib subprocesses, with no
external/GPU/paid compute, network access, hardware, credentials, live sensor,
notifications or ToolBackend dispatch. The DB files are independent; their
readings are NOT a globally atomic cross-store snapshot. No trusted human
issuer, signed clock, real backend outcome attestation, automatic external
WRITE replay or Candidate generation exists.

Next: validate the post-COMMIT audit constructor-fault regressions and its
exact-head six-runner CI, improve recovery of independent stored prefixes and
revocation history, and continue Memory CAS/expiry and privacy-safe synthetic
snapshot integration without changing frozen contracts.
