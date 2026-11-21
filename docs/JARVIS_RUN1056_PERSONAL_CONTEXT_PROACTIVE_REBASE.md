# Run1056 — Personal Context replay crash and proactive race fixture rebase

## Exact work basis

- Parent branch: `research/jarvis-foundations`.
- Exact parent HEAD: `b973d9e4e5d4ecdd9912a92274622d07ab23748f` (after the exact-head-GREEN Run1055 Memory SQLite path-admission integration).
- Child branch: `research/run1056-personal-context-proactive-rebase`.
- Scope: test-only; no production source changes.

## Personal Context replay COMMIT crash boundary

A spawned child exits immediately after native SQLite COMMIT and before `reserve()` can construct or return its local receipt. Cold recovery checks one hash-only reservation, stale/duplicate denial, SQLite integrity, and absence of synthetic private fixture text from durable bytes.

The test uses disposable local SQLite and deterministic synthetic context fixtures only. A local witness is not consent, revocation freshness, disclosure permission, independent custody, trusted time, authenticated provenance, or exactly-once external action evidence.

## Proactive two-process race fixture

The test keeps a parent SQLite connection in WAL mode while two child processes race preparation. This keeps legitimate WAL/SHM sidecars linked during the fixture and avoids nondeterministic DELETE-journal sidecar unlink observations. Production path checks and the process race remain unchanged; no production guard is relaxed.

## Validation limits

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed. The package performs no live personal-data access, disclosure, notification, ToolBackend dispatch, external effect, trusted-clock operation, paid service, external compute, Candidate generation, protected V2 evaluation, frozen-contract change, UI work, or main merge.

PR #8 remains Draft/unmerged. ARK/JARVIS remains NOT_PASSED.
