# ARK AI Run1020 — Personal Context replay reservation process-crash boundary

**Work basis:** Draft PR #8 branch `research/jarvis-foundations`, exact HEAD `ff3e9e50ca861486a667bce243ee6ca62af08e28`. This is a test-only child; PR #8 remains OPEN/DRAFT/UNMERGED.

## Finding

The existing replay-ledger COMMIT-UNKNOWN test injects a lost acknowledgement in-process. This package adds an OS-process exit immediately after native SQLite COMMIT and before `reserve()` can construct or return its local receipt.

## Regression

A spawned child reserves one synthetic request, commits natively, then exits with a dedicated code from the wrapped connection's `commit()` method. The parent requires:

- the child exited at the post-COMMIT boundary, not by returning normally;
- cold reopen observes exactly one hash-only reservation and a clean SQLite `quick_check`;
- the original genesis witness is stale and cannot append another request;
- a fresh local witness still cannot reserve the duplicate request ID;
- the row contains no fixture context text and the witness/ledger remain denial-only.

The test is authored; no local pytest/Ruff PASS is claimed. Exact-head Ubuntu/Windows × Python 3.11–3.13 CI is required.

## Limits

Synthetic fixture text and identifiers, spawned local processes and disposable SQLite only. A process-local witness is not independent custody, consent, revocation freshness, disclosure permission, trusted time, authenticated provenance, or exactly-once external action evidence. No live personal data, external service, ToolBackend, production source, frozen contract, Candidate, protected evaluation, UI, PR #5, PR #9, or main branch is changed.
