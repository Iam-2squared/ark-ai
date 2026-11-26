# ARK AI — Memory expiry, startup integrity, revocation scope callback epochs (Run402)

## Scope and authorization status

This engineering note documents **five independent, offline and reversible**
source/test packages on Draft PR #8. It is a threat model, not a PASS claim for
JARVIS, a trustworthy issuer, a real ToolBackend, or privacy consent. This run
does not open protected evaluations, train a Candidate, create an adapter, touch
frozen V1/V2/Local UI/Launcher evidence, amend Memory v1 DDL, send notifications,
read real personal data, or permit external action.

All security claims below apply only to the exact local Python/SQLite fixture
boundary. Frozen dataclasses are reflectively mutable in Python; a user-supplied
iterator, predicate, digest helper, or patched validator may execute hostile
code. Merely recomputing a digest at operation end is insufficient if an earlier
mutable carrier is changed and subsequently restored between callbacks.

## Package A — coherent Memory snapshot expiry predicate

**Files:** `src/ark/memory/coherent_snapshot_review.py`,
`tests/test_memory_snapshot_expiry_epoch_run402.py`.

**Prior exposure:** The `_expired(record, now)` predicate previously ran in
a list comprehension, without checking original request, store path, and all
decoded MemoryRecord carriers between individual predicate invocations.
For a three-record snapshot, predicate #2 could mutate record #1, its scope,
the request namespace, or the store path, and predicate #3 could restore the
original values before ranking. A final-only epoch check could miss it.

**New invariant:** Before and after **each** predicate, verify pinned request,
path and records. On drift, raise `MemorySchemaError` and return **no partial
snapshot**. Existing SQL selection, <=10,000 physical rows per namespace,
rank ordering, clock sample, read-only transaction, digest format and Memory v1
schema remain intact.

**Synthetic regressions:** Four attack cases (earlier record, nested scope,
request, same-value Path replacement) plus normal unmodified and
`include_expired=True` bypass-of-predicate cases: **6 tests**. The tests
assert denial occurs before the third predicate could restore drift.

## Package B — cached startup readiness integrity callbacks

**Files:** `src/ark/startup_readiness_review.py`,
`tests/test_startup_snapshot_integrity_epoch_run402.py`.

**Prior exposure:** `StartupSnapshot._assert_integrity()` validates individual
identifiers and serializes/hash-checks a dependency graph. A patched
`_identifier` could mutate a previously inspected component and restore it
on the next identifier call; likewise a patched JSON encoder could mutate
the cached snapshot and a hash helper could restore it. Internal graph and
digest checks performed only at the end could accept that transient drift.

**New invariant:** Retain the original `components` tuple, each
`ComponentResult` object and all structural/state carriers. Re-check after
every identifier validation and around JSON serialization and hashing.
Equal-valued replacement of the original tuple is also rejected. This is
an *epoch-consistency diagnostic*, not an authenticated startup probe nor
proof that a real tool is safe to start.

**Synthetic regressions:** Three first-callback mutation cases (local state,
schema revision, equal-valued outer tuple replacement), one JSON-vs-hash
reflection case, and one unchanged BLOCKED dependency check: **5 tests**.

## Package C — local Personal Context revocation scope at ingress

**Files:** `src/ark/personal_context_revocation_review.py`,
`tests/test_revocation_initial_scope_epoch_run402.py`.

**Prior exposure:** `revoke(scope)` computed its **first** scope digest before
capturing the original owner/namespace. An instrumented digest callback could
retarget the incoming `MemoryScope` to a different syntactically valid owner
or namespace; subsequent checks would validate and persist the **wrong**
scope's veto.

**New invariant:** Capture the original exact `MemoryScope` owner/namespace
before the first digest, check after that callback, during SQLite validation,
after the second digest, and immediately before committing. A rejected initial
digest leaves **zero inserted veto rows**. Existing rows are neither deleted
nor reenrolled.

**Synthetic regressions:** Two first-digest retargets (owner and namespace)
plus one normal exact-scope veto/adjacent-scope isolation: **3 tests**.

## Package D — restart-safe negative mock integration evidence

**File:** `tests/test_mock_cycle_restart_nonreplay_run402.py` (six cases).
This test-only integration lane reopens **all four** independently committed
SQLite stores—Planner journal, occurrence ledger, ActionAudit and occurrence/
audit sidecar—after each of five injected stop boundaries: after RUNNING,
reservation, pre-action audit, audit link and in-memory mock marker. It records
the number of persisted reservations, audit rows and sidecar links both before
and after the attempted restart, and asserts that none increase on retry.
The Planner must recover RUNNING as ambiguous and refuse the second WRITE,
regardless of which other local stores show apparently consistent evidence.
A sixth case verifies that a completed *local mock* also cannot replay after
reinitialization. Each fixture registration uses an executable that raises
unconditionally on invocation; it must observe **zero backend calls**.

This is not a real process-kill test or proof of atomic cross-store
transactions. Each stop is an explicit exception at a named fault boundary,
not an OS crash. The test does not simulate arbitrary syscall interleavings,
disk corruption, external network effects, human approval, or real clock
provenance. Its sole claim is exact-head regression coverage for disconnected,
conservative UNKNOWN and no-replay behavior.

## Package E — Planner retained tail must survive first callbacks

**Files:** `src/ark/agency/planner_journal_review.py`,
`tests/test_planner_retained_ingress_epoch_run402.py` (**5 cases**).

**Prior exposure:** Both `SyntheticPlanJournal.recover(retained=...)`
and `append(retained=...)` constructed a PlanGraph/topology digest and called
`retained.assert_shape()` before pinning that caller-supplied retained
evidence. A reflective callback could replace the independent retained tail
with an *equally valid but older* prefix, causing the later history check to
validate a different witness than the one supplied at entry.

**New invariant:** Capture all five original tail fields before the first
topology/shape callback. Refuse changes immediately after `assert_shape()`
and preserve later checks inside transaction/recovery. Four tests attack both
APIs from two callback positions; a fifth verifies normal retained-prefix
recovery and CAS append. A failed append leaves the original RUNNING transition
unchanged, and a RUNNING WRITE is never automatically retried. No real
backend, human issuer, filesystem attestation or trusted clock is introduced.

## Integration and non-proofs

These five packages are separate so a CI run for one module can proceed while
another module is developed. All tests are offline, deterministic fixtures.
Source/test CI should be evaluated on the **exact final source/test HEAD**
across Ubuntu and Windows with Python 3.11–3.13; a later documentation
checkpoint must be validated separately. This document intentionally does not
claim CI completion until those GitHub job results are observed.

Important gaps remain: a Python in-process reflection guard is **not**
kernel-mediated file descriptor/inode custody; local content digests are not
signed/independently retained attestation; SQLite snapshots spanning distinct
stores are not atomic; system wall-clock is not a trusted execution clock;
revocation absence does not imply consent; STARTUP READY grants no permission;
a local audit receipt cannot prove external WRITE success. Unknown external
WRITE results must remain UNKNOWN and **must not automatically replay**.

## Next plan / 今後の方針

1. Observe final exact-HEAD CI, repair real regressions via ordinary GitHub
   source/test writes if needed, and keep unfinished jobs labeled IN PROGRESS.
2. Compose a strictly disconnected Planner/Registry/PermissionGate/
   occurrence/ActionAudit/mock executor crash-recovery fixture with explicit
   restart and UNKNOWN non-replay; first bind the existing lower-level GREEN
   evidence and avoid external dispatch.
3. Review Memory CAS/expiry/coherent snapshots and Personal Context revocation
   lifecycle; keep personal data private and cross-store atomicity unclaimed.
4. Develop fail-closed, offline trusted-clock/human-issuer *ports*, not
   fabricated approval or live execution; continue Observation/Scheduler and
   V3 free-only provenance guard lanes with their paid/frozen gates closed.
