# ARK AI Run1019 — Memory generation CAS rollback before native COMMIT

**Work basis:** Draft PR #8 branch `research/jarvis-foundations`, exact HEAD `8ac44aabbc8a65b620aa0ccc74ffa44d711a3c8a`. This is a test-only child; the parent remains OPEN/DRAFT/UNMERGED.

## Finding

Run1018 PR #67 covers native SQLite COMMIT success followed by a lost acknowledgement for generation-fenced Memory update. Existing event-insertion rollback tests cover failures before COMMIT, but did not isolate a SQLite error raised at the generation-CAS COMMIT boundary before native COMMIT.

## Regression

The new test wraps only the disposable Memory writer connection. Its context-manager exit simulates the rollback outcome and raises `sqlite3.OperationalError` without invoking native COMMIT. It requires:

- generation CAS reports SQLite outcome uncertainty rather than success;
- cold reopen retains the original revision-1 row and its single `create` event;
- read-only triage reports `LOCAL_UNCHANGED`;
- caller attribution, automatic retry, write authority and trusted-clock claims remain denied;
- the row/event pair remains unchanged after triage.

The test is authored; no local pytest PASS is claimed. Exact-head Windows/Linux × Python 3.11–3.13 CI is required.

## Limits

Synthetic scope/content/metadata, deterministic local clocks and disposable SQLite only. This is not power-loss/fsync durability, authenticated writer provenance, independent custody, trusted time, consent, retention authorization, cross-store atomicity, or exactly-once external effects. Memory v1 schema/public API and frozen contracts are unchanged. No live personal data, ToolBackend, paid service, external compute, credentials, Candidate, protected V2 evaluation, UI, PR #5, PR #9, or main branch is changed.
