# Run549 — detached READ authority and Memory CAS post-COMMIT result custody

**Scope:** zero-new-cost, local-only JARVIS foundations; PR #8 Draft and
unmerged. These reviews do not execute a ToolBackend, authenticate a person or
clock, prove outside-world results, grant consent, replay an action or touch
frozen Memory/Planner contracts.

## 1. Detached READ recovery evidence / denial descriptors

Source: `src/ark/agency/disconnected_read_recovery_journal_bridge.py`
at `1395efc3242fd50f4c292de14d6c62b2cf2df665`.
The existing read-only join of a recovered synthetic READ DAG and retained
SQLite journal chain already checked result and receipt bytes. The Run549
change also pins original class-level non-authorizing descriptor objects
for `ReadJournalSnapshot`, `ReadJournalWitness` and
`ReadRecoveryJournalReview` **before** the replaceable schedule callback.
Subsequent stability checks reject even a replacement `property` returning
the exact `False` value. That matters because a false-only accessor is still
an executable callback with potential to alter earlier evidence.

Tests: `tests/test_detached_read_recovery_descriptor_custody_run549.py`
at `f1189e9546838a1aaad9fa8fa9c9fc01d0f44451`.
**13 authored parameter-expanded cases:** twelve replaced-denial getter
variations across all three carrier classes, plus an unchanged safe control.
Exact-head CI [41395642789](https://github.com/Iam-2squared/ark-ai/actions/runs/41395642789)
was **IN PROGRESS** at evidence capture (3 Ubuntu jobs GREEN, 3 Windows
jobs in progress). No GREEN claim is inherited by a newer HEAD.

## 2. Memory generation-fenced CAS returned record after COMMIT

Source: `src/ark/memory/generation_fenced_cas.py` at
`002c3800886ebf77ad47e17222ae74f99bc2ce4d`.
Previous code checked updated row/event invariants inside SQLite
`BEGIN IMMEDIATE`, then checked only original write/token inputs after
the connection context completed its COMMIT. A synthetic connection-exit
callback could rewrite the previously hydrated `updated` MemoryRecord
(or its generation token) **after the durable COMMIT**, causing a forged
object to be returned. The new code captures result field carriers,
metadata and generation token before the close/COMMIT boundary, then
rechecks exact carriers, metadata, token and row digest afterward.

Tests: `tests/test_memory_cas_postcommit_result_custody_run549.py`
at `237183e9b9c3c6249d62d93d17da1eee84223fb9`.
**7 authored cases:** six mock SQLite connection-exit mutation injections
(record content, revision, digest, metadata, token row digest or event ID),
plus a normal successful committed update. Mutation exceptions are
**post-COMMIT ambiguous outcomes, never evidence of rollback or permission
for automatic retry**. The tests verify the SQLite row/event actually
persisted exactly once even when the returned carrier is denied. Latest
source-and-test CI
[41396032613](https://github.com/Iam-2squared/ark-ai/actions/runs/41396032613)
was **IN PROGRESS** at evidence capture. Do not classify newer HEADs
as GREEN without fresh exact-head checks.

## Remaining gates and follow-up

Continue linking durable READ/Planner/registered mock receipt evidence only
after the corresponding tests are GREEN. Strengthen Memory manual-only
COMMIT-UNKNOWN triage and independent retained-witness custody without
retrying ambiguous writes. Preserve frozen V1/V2/Memory v1 contracts,
protected V2 gates, all real ToolBackend/external actions, explicit
approval requirements, PR Draft boundaries and the ban on billable compute.
