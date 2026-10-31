# Run405 — plan-wide registry subject, Memory setup and synthetic clock carrier integrity

Scope: reversible disconnected foundations in Draft PR #8. This document records
the source-level safety contract and negative fixture boundaries, not an ARK
PASS, permission grant, human approval, or external outcome proof.

## A. Plan-wide WRITE recovery: verify the identity actually bound

Files:

- `src/ark/agency/synthetic_write_plan_recovery_review.py`
- `tests/test_synthetic_write_plan_binding_epoch_run405.py`

The plan-wide reviewer pins all original PlanStep carriers, the exact ToolCall
object, its argument carrier and its primitive tool/capability/scope and
arguments digest **before** its first registry bind. After binding, it refuses
a result whose `bound.call` is not the original, request identity or registry
revision differs, or whose registration is not the immutable ToolRegistry entry
for the original tool. The subsequent epoch check follows the registry lookup.

Fault fixtures cover an adversarial in-process bind callback that temporarily
retargets a WRITE to a valid READ and restores the WRITE fields before
returning; a bind result for another ToolCall; forged bound revision; and
substituted registration. A valid dependent two-WRITE fixture remains inert.

This specifically closes the risk that `bound.registration.effect` alone
could silently omit an original WRITE from a plan-wide recovery diagnosis.
The result still never authorizes dispatch or replay. Ordinary Python callback
reentrancy detection is not an integrity boundary against a malicious host,
dynamic module replacement or external side effects.

## B. Coherent Memory snapshot: read-transaction setup epochs

Files:

- `src/ark/memory/coherent_snapshot_review.py`
- `tests/test_memory_snapshot_sqlite_setup_epoch_run405.py`

Recheck the original request, namespace/scopes and SQLite Path after each
reentrant setup boundary: `row_factory`, `PRAGMA busy_timeout`, `BEGIN`,
the first schema read and `PRAGMA user_version`. The read-only handle is
closed on a mismatch. This protects against a callback changing an earlier
scope, restoring it in the *next* SQLite statement, and escaping a later-only
check. Four disposable SQLite connection-factory fault positions are covered.

The existing Memory v1 DDL, event semantics, retention gates and per-namespace
scan budget are not changed. This is a single-database coherent read only;
it is not a distributed snapshot, storage-device identity attestation,
automatic privacy erasure or permission to share Personal Context.

## C. Caller-provided clock samples: carrier preservation and early budget

Files:

- `src/ark/agency/synthetic_clock_sequence_review.py`
- `tests/test_synthetic_clock_carrier_budget_run405.py`

A retained clock witness's source and chain string carriers are pinned by
identity in addition to content; a previously yielded sample's source string
cannot be swapped for a value-equal clone during a later yield or
`StopIteration`/generator finalization. An impossibly large retained prefix
(`retained.event_count > max_samples`) is rejected **before** constructing
or consuming the caller's iterable. Valid retained-prefix extension remains
accepted.

Local sequence monotonicity, chain consistency and bound checks **do not**
authenticate clocks or timing provenance. Witnesses always remain
`trusted_clock_verified=False`, `dispatch_authorized=False`,
`automatic_replay_authorized=False`. No clock device, OS clock, issuer,
backend, secret, credential, external service or GPU is accessed.

## D. All-WRITE recovery: caller-retained prefixes across four stores

Files:

- `src/ark/agency/synthetic_write_plan_recovery_review.py`
- `tests/test_synthetic_write_plan_retained_prefix_run405.py`

The plan-wide review now optionally accepts exact-type retained PlanTail,
reservation LedgerWitness, audit ContinuityWitness and occurrence-audit
LinkWitness. A retained link cannot be provided without its sidecar store.
All prior witness object fields are pinned before validation and rechecked at
every cross-step callback. The exact same retained prefixes are forwarded
to **every WRITE step's** read-only recovery, the repeated first-step review,
and the final plan replay.

Restart fixtures exercise a stable four-store reopen; a replaced empty
journal that loses a RUNNING WRITE; an empty replacement ledger that erases
a previously witnessed orphan/PENDING reservation; an empty audit store that
drops a witnessed local event; a missing sidecar; and a value-equal reflected
replacement of a retained digest carrier during the first WRITE's callback.
Without separately retained witnesses, a fresh empty store may look locally
consistent; this extension is designed to reject *witnessed* rollback instead
of incorrectly treating a fresh local PENDING state as evidence of safe replay.

The original writes remain synthetic, the result stays inert, and independent
SQLite reads are not an atomic cross-store snapshot. The retained witnesses
are explicitly caller-supplied and must be kept outside mutable fixture stores
to carry any continuity value; they are neither signed provenance nor receipts
for an external WRITE.

## E. Observation window witness: final serialization and hash epoch

Files:

- `src/ark/observation_window_review.py`
- `tests/test_observation_window_witness_digest_epoch_run405.py`

The read-only observation window's `witness` first validates its retained
envelopes and privacy scope, then serializes the metadata-only payload and
calculates its local SHA-256. It now **revalidates** the original envelope
identities and content **after serialization and after hashing**, before
returning a cached-looking witness. Fault fixtures replace envelope source/
content fields while `json.dumps` executes, temporarily change them and
attempt restoration from `hashlib.sha256`, and mutate them during the digest
callback itself. A normal deterministic witness remains unchanged.

Previously, a final serialization/digest callback could leave the carrier
changed after the last integrity check while the function still returned an
apparently valid witness for older fields. This closes that local race; it
does not authenticate content provenance, camera/microphone access, user
consent, or later use by a real scheduler.

## CI, limitations and authorization gates

Each individual GitHub HEAD requires its own exact-head CI. Tests added here
are regression cases; do not report a combined PASS before the corresponding
CI jobs actually complete GREEN. The incremental source writes and tests were
saved using ordinary GitHub Contents API on the isolated Draft PR #8 branch.
No raw Git object/ref bypass, force push, workflow rerun or main merge.

Cross-store journal, reservation, audit and link histories still have no atomic
multi-database snapshot. UNKNOWN WRITE is not safe to replay, even if a
locally successful mock or an apparently matching diagnostic exists. No
authenticated consent, trusted clock, live backend receipt, real exactly-once
proof, Candidate training or protected V2 final evaluation was produced.
Frozen V1/V2/Local UI/Launcher and V3 paid/promote boundaries stay closed.

## Next plan / 今後の方針

1. Confirm exact-head Ubuntu/Windows Python 3.11–3.13 jobs and Ruff. Repair
   only observed regressions without relaxing deny conditions.
2. Extend all-WRITE diagnosis to independently retained **plan / occurrence /
   audit / sidecar** prefixes, so restart truncation cannot silently downgrade
   a previously seen reservation to a clean PENDING step.
3. Build bounded two-WRITE crash/restart fault matrices with dependent steps,
   orphaned reservations, local SUCCEEDED markers and cross-store drift.
4. Continue privacy-safe Memory/Context, scheduler/observation and deny-by-
   default clock/issuer design, without enabling real side-effect dispatch.
