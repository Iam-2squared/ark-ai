# Run530 — SQLite Memory event lifetime timestamp coherence

**Scope:** Draft PR #8, local-only, read-only audit. Work basis `b8fe9b5aaa2fae8bade501f5376e5ec3b3beabee`. Source change `eeaf0ce2d063b3581958081e6258df912aeec98d`; authored tests `0b30a6716c2c5657d9f63d105363df0fb9d478f8`; corrected test event count `81f498abf054769cdca49053b9b574287c556a3a`; corrected Ruff F821 fixture `e50665b6fbb8fc74a9e797bef062abbd17df055f`.

## Previously incomplete invariant

`review_memory_event_alignment` checked local CREATE/UPDATE/DELETE/EXPIRE transitions and matched a live row's owner, namespace and revision. However, it did not reconcile that row's **created_at_ms and updated_at_ms** against the live cycle's CREATE event and most recent CREATE/UPDATE event.

This permitted a syntactically valid SQLite v1 row or event to have forged storage timestamps while the read-only audit reported its lifecycle consistent. The independent `expiry_candidate_preview` recently added a scoped per-candidate version of that check, but the whole-store audit still lacked it.

## Implementation

The all-scope audit now tracks `(owner, namespace, revision, active, current_cycle_created_at_ms, last_write_at_ms)` for each event stream inside the **same SQLite read transaction** as live rows. CREATE starts a lifetime, UPDATE advances revision and updates the last-write timestamp, DELETE/EXPIRE closes that lifetime, and CREATE after terminal starts a new one. Before returning its local digest, each active state's `(owner, namespace, revision, created_at_ms, updated_at_ms)` must exactly equal its persisted row.

No chronological monotonicity is assumed: the v1 store accepts a bounded integer caller-supplied clock that may regress. Requiring monotonic wall time here would silently change an existing accepted v1 contract. Instead, the audit checks **equality of the row and the corresponding events**.

## Focused tests and CI

`tests/test_memory_event_timestamp_alignment_run530.py` authors **7 cases**: four row/event timestamp drifts rejected, delete/recreate timestamp reset, legitimate backward clock with matching events, and a coordinated local SQLite edit producing a *different* untrusted content-free audit digest.

[PR8 CI 41308076231](https://github.com/Iam-2squared/ark-ai/actions/runs/41308076231) failed 6/6 at Ruff because a test fixture referenced `scope` after an unused-variable cleanup. This was a test-only bug, not an audit-guard failure. The correction replaces that reference with `second.scope` at `e50665b6fbb8fc74a9e797bef062abbd17df055f`, without changing the actual Memory source or rejection semantics. The corrected head requires its **own** CI; earlier GREEN never transfers to this new head.

## Limitations

This verifies a bounded read-only local SQLite observation. Both rows and events may still be coherently rewritten by an untrusted local actor unless an independently retained, authenticated digest exists. Neither SQLite time nor hashes prove a trusted clock, owner, consent, external custody, privacy-disclosure permission, deletion or physical erasure. V1/v2 frozen contracts and main were not edited, no purge was called, PR #8 stays Draft, and ARK/JARVIS completion stays **NOT_PASSED**.
