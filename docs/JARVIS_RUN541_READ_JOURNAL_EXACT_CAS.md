# Run541 — detached registered READ journal exact CAS

**Scope:** isolated local SQLite fixture, normal GitHub Contents writes, no real ToolBackend, external compute, consent or automatic replay.

## Source and test evidence

- Work-basis HEAD immediately before this package: `cd9fa4bc19361480cd217c2796f07b3642c20b6c` (separate Run541 Planner/Memory/Scheduler packages and technical note retained).
- Source commit: `a32a88996e6576b05c5a3926f05cfe73ad75a9b6` — `src/ark/agency/disconnected_read_journal.py`.
- Test commit: `6dc4fa5c3f0ab6eb150d06c326280b4bc47af3da` — `tests/test_read_journal_patched_equality_cas_run541.py`, **5 authored parameter-expanded pytest cases**.
- After inspecting actual CI failures in the independent WRITE-restart test, the expected rejection-message assertion was corrected *without changing any production rejection semantics*: `373414c833c8943fefbb6f5c4ab104281f45fae8`, `tests/test_write_restart_final_callback_custody_run541.py`.

## Correctness property

The detached synthetic READ journal's append CAS previously tested `actual != retained`, implicitly invoking a replaceable `ReadJournalWitness.__eq__` method. A test fixture can override this method to always report equality and permit a stale witness to bypass the optimistic revision comparison.

The guarded path now compares `actual.count` and `actual.tip_sha256` independently against the already pinned retained count and tip. Tests inject stale genesis witnesses, a correct count with forged tip, a wrong count with current tip, and hostile always-True/always-False equality callbacks. Only the exact current retained witness can extend the local chain.

The journal is **not** external evidence of real READ action completion, a registered ToolRegistry identity, true cross-store atomicity, human authorization or trusted time. Its opt-in append has post-COMMIT ambiguity and must not be blindly repeated.

## CI evidence boundary

The inherited Run540 PR #8 HEAD `a54f0d1cbb3722e972afdc6261eb8091a76f6837` was verified with all six CI jobs GREEN at [41354812977](https://github.com/Iam-2squared/ark-ai/actions/runs/41354812977). New Run541 HEADs require their own CI checks. The first WRITE-restart test run [41358873768](https://github.com/Iam-2squared/ark-ai/actions/runs/41358873768) failed on **one test assertion message mismatch** ("carriers changed" expected, actual "WRITE restart step changed"), while the observed Ubuntu 3.12 job reported 6610 passed, one skipped, one failed. This was corrected by the minimal test-only commit above. New source+test HEAD success is **not claimed until independently observed**.

## Next

Inspect PR #8 latest exact HEAD CI; do not retry equivalent runs or erase the first failure. Independently test higher-level registry-bound receipt joins after lower-level invariants GREEN. Preserve Draft PRs, frozen contracts and approval boundaries.
