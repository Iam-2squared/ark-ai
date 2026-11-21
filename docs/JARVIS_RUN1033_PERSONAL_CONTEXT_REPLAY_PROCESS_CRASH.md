# ARK AI Run1020 — Personal Context replay reservation process-crash boundary

**Rebase work basis:** Draft PR #8 branch `research/jarvis-foundations`, exact HEAD `e53ffc7db904584a1e817fcfb544012d75eeafc0`. Rebased from PR #75's test-only package; PR #8 remains OPEN/DRAFT/UNMERGED.

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


## Run1030 rebase onto the current foundation head

- New exact work basis: Draft PR #8 branch `research/jarvis-foundations`, HEAD `b585c61a6e3ca1a9f456175b2a96053a908a500c`.
- Re-applied as a test-only child after the PR #8 checkpoint commit; no production source or frozen contract is changed.
- Previous child PR #98 head `0885d943b594b76e35c956fe790ed10b86108f40` had exact-head CI run #44795939814 GREEN (6/6). That evidence applies only to the previous head and is not transferred to this new rebase.
- Original pre-rebase regression evidence was CI run #44731478084; it is historical evidence only.
- Fresh exact-head six-job CI is required. No local pytest/Ruff PASS is claimed.


## Run1031 rebase onto the latest foundation checkpoint

- Exact work basis: Draft PR #8 branch `research/jarvis-foundations`, HEAD `7d25d985c613a36bf81bf4fa11c0fbaea4928b11` (the Run1030 checkpoint commit).
- Re-applied as a test-only child using synthetic fixtures and disposable local SQLite. No live personal data or disclosure path is involved.
- Previous Run1030 rebase head `0238ec6e937a994beb1ce05562315971ba852010` passed exact-head CI #44804593658 (6/6) on its earlier base. That result is historical and is not transferred to this new head.
- Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed.


## Run1032 rebase onto the latest foundation checkpoint

- Exact work basis: Draft PR #8 branch `research/jarvis-foundations`, HEAD `7e7d737195229154775d06baa5b1d8e5c230882b` (the Run1031 checkpoint-result HEAD).
- Re-applied as a test-only child; Personal Context source, privacy contract and main are unchanged.
- Previous Run1031 child head `3af91b11f354a10754cb552d31d5e86aa3da4fce` passed exact-head CI #44814358907 (6/6) on its earlier base. That result is historical and is not transferred to this rebase.
- Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed.


## Run1033 rebase onto the latest foundation checkpoint

- Exact work basis: Draft PR #8 branch `research/jarvis-foundations`, HEAD `c92ef6d65df5e79349e3fa534902117bdfcf263b` (the Run1032 checkpoint-result HEAD).
- Re-applied as a test-only child with synthetic fixtures and disposable local SQLite; no live personal data or disclosure path is involved.
- Previous Run1032 child head `bd35ccfefa870bf50b6eb47f2a62dcfdac7ee3a2` passed exact-head CI #44823908761 (6/6) on its earlier base. That result is historical and is not transferred to this rebase.
- Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed.
