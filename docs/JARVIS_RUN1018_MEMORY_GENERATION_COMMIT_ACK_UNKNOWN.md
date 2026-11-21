# ARK AI Run1018 — Memory generation CAS COMMIT-UNKNOWN

**Work basis:** Draft PR #8 branch `research/jarvis-foundations`, exact HEAD `40c3467d6e45c477780f1c83b2a1cfa53111f932`. This is a test-only child; the parent remains OPEN/DRAFT/UNMERGED.

## Finding

The opt-in generation-fenced Memory update already treats SQLite errors from its write transaction as UNKNOWN and never retries. Existing tests cover post-COMMIT readback failures, post-COMMIT input/result mutation, independent-handle ambiguity, and abrupt exit before COMMIT. They did not explicitly exercise a native SQLite context-manager COMMIT that succeeds while the acknowledgement is lost.

## Regression

The new test wraps only the disposable writer connection. Its `__exit__` delegates to the native SQLite connection, confirms that the native commit returned, then raises a synthetic `sqlite3.OperationalError`. It requires:

- the update API reports `generation CAS SQLite outcome uncertain`, not success;
- cold reopen sees exactly the revision-2 Memory row and matching `create/update` event pair;
- read-only triage reports one matching update but does not authenticate caller attribution or authorize retry/write/trusted time;
- the original generation token cannot append another update;
- the persisted row and event history remain unchanged after the stale-token attempt.

The test is authored; no local pytest PASS is claimed. Exact-head six-job CI is required.

## Limits

Synthetic scope/content/metadata, deterministic local clocks and disposable SQLite only. This is not power-loss/fsync durability, authenticated writer provenance, independent custody, trusted time, consent, retention authorization, cross-store atomicity, or exactly-once external effects. Memory v1 schema/public API and frozen contracts are unchanged. No live personal data, ToolBackend, paid service, external compute, credentials, Candidate, protected V2 evaluation, UI, PR #5, PR #9, or main branch is changed.
