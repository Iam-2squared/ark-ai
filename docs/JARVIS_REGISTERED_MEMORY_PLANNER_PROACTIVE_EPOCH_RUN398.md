# Run398 — Registered grants, Memory purge, Planner tail, Proactive witness custody

**Scope:** FREE-only, public-repo, opt-in synthetic/offline foundation hardening on
`research/jarvis-foundations` (Draft PR #8). No existing `main` files or frozen
V1/V2/Local UI/Launcher contracts, Memory v1 SQL DDL, or protected evaluation
evidence are changed. This engineering record is not a PASS declaration.

## Failure modes and improvements

### A. Registry-bound PermissionGate — rebind callback epochs

**Code:** `src/ark/agency/policy.py`  
**Regressions:** `tests/test_registered_rebind_grant_epoch_run398.py` (16 parameter cases).

The first registry bind and each grant yield already had pre- and postchecks.
However, a second registry bind could reflectively modify an earlier, already
materialized `CapabilityGrant`; the following general-purpose policy evaluation
would then snapshot the *changed* grant as if it were originally reviewed.
An under-token-lock registry bind could likewise mutate a previously checked
grant after the general-purpose spend check. Both paths must fail closed
**before** spending the mock in-process one-shot token.

The registered path now rechecks the original grant epochs immediately after
its second bind and both before and after every registered identity rebind
(including the callback made inside `authorize()` while holding the token lock).
Invalid reflected grant fields map to `PermissionDenied` instead of escaping
as an unrelated Python error. No actual backend is invoked. Normal unchanged
READ and WRITE fixtures remain accepted; WRITE only consumes a process-local
one-shot marker, not authenticated human authorization.

### B. Multi-row Memory purge — between-event drift

**Code:** `src/ark/memory/sqlite_store.py`  
**Regressions:** `tests/test_memory_purge_row_epoch_run398.py` (7 parameter cases).

The earlier purge implementation checked the owner/scope and SQLite Path at
transaction entry and before final commit. An injected `_record()` callback or
the first `_event()` callback could change the caller scope or Path, while a
later row callback restored it. This could bypass the final-only check.

The new row-phase fence checks original owner/namespace and exact Path carrier
before and after each hydration and immediately after each event append.
A mismatch raises `MemorySchemaError`, causing the current SQLite
transaction to roll back **both** the expiry deletions and their event inserts.
It does not change the frozen Memory v1 schema or claim OS-level inode custody.

### C. Planner append — witness mutation after snapshot

**Code:** `src/ark/agency/planner_journal_review.py`  
**Regressions:** `tests/test_planner_append_retained_snapshot_epoch_run398.py` (3 parameter cases).

A synthetic Planner append used to validate the independently retained
historical `SyntheticPlanTail` before building the outgoing snapshot. Snapshot
construction is an observable callback boundary: a reflected mutation of an
already validated older tail could occur after the earlier check, yet its new
row/header changes would still commit. The append now revalidates retained tail
shape and its originally pinned values immediately before the final source and
topology checks and transaction COMMIT. On disagreement the journal rolls back
the event **and** header update together. A recovered RUNNING step remains
ambiguous/UNKNOWN; no external WRITE replay permission follows.

### D. Proactive Scheduler — exact retained row carrier

**Code:** `src/ark/proactive_synthetic_review.py`  
**Regressions:** `tests/test_proactive_retained_tuple_epoch_run398.py` (2 cases).

An independently retained trigger-history witness previously pinned row values,
but allowed the `row_hashes` tuple to be replaced by a distinct value-equal
carrier during its integrity or history-comparison callback. The preparation
transaction now pins both tuple *identity* and values at entry, after initial
witness validation, before and after the historical comparison inside the
writer transaction, and before committing a new synthetic preparation marker.
The mismatch rejects the new admission without persisting a second occurrence.
No notification, real scheduler activation, consent or ToolBackend is supplied.

## Evidence and limits

Each regression suite deliberately uses reflected frozen-object mutations and
disconnected/mock callbacks, then inspects rejection and transaction/token
effects. These are **local negative fixtures**; they do not prove immunity to
arbitrary malicious code in the same process. An attacker with direct access to
private fields, clocks, or the SQLite files may still coordinate a rewrite.
No trusted wall clock, authenticated issuer, signed external receipt, durable
cross-process exactly-once guarantee, atomic cross-SQLite snapshot, or real
hardware/backend execution is established.

CI results must always be attributed to their **exact GitHub commit SHA**.
Source/test commits are separate ordinary GitHub Contents writes, so any CI
result on a source-only intermediate head does not validate the subsequent
test commit. See the newest `docs/PROJECT_STATUS.md` checkpoint for observed
run IDs and actual job conclusions; never extrapolate GREEN from an ancestor.

## Required gate preservation

- V3 PR #5 stays Draft, unmerged, NOT_PASSED; Contract 1 and protected V2 FINAL
  remain frozen. No Candidate/adapter/weights, preflight GPU step, paid compute,
  billable API, new credentials, or user approval is inferred.
- PR #8 stays Draft, isolated from `main`. No physical-PC actions, secrets,
  real media acquisition, notification dispatch, ToolBackend WRITE or merge.
- Only normal GitHub Contents file writes are used, after inspecting the latest
  branch HEAD. No raw Git objects/refs, force-push, bypass, or duplicate CI run.
- The next integration gate is an exact-head GREEN suite **plus** independent
  review of durable identity/consent/trusted-clock/UNKNOWN-result semantics,
  not merely a growing local unit-test count.
