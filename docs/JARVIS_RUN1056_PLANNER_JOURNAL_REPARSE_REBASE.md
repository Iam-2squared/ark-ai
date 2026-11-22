# Run1056 — Planner journal Windows reparse-point admission rebase

## Exact work basis

- Parent branch: `research/jarvis-foundations`.
- Exact parent HEAD: `b973d9e4e5d4ecdd9912a92274622d07ab23748f`.
- Child branch: `research/run1056-planner-journal-reparse-rebase`.
- Source: `src/ark/agency/planner_journal_review.py`.
- Regression: `tests/test_planner_journal_reparse_point_ancestry_run1055.py`.

## Finding and change

The disconnected replay-only Planner journal rejected POSIX symlinks, unsafe ancestors, hardlinked leaves and SQLite sidecars, but Windows junctions/reparse points can retain ordinary directory/file mode bits. This rebase pins the Windows reparse mask, rejects malformed present metadata, checks ancestors/database leaf/SQLite sidecars before SQLite use, and inspects the main leaf with `lstat` rather than following it through `exists()`.

The journal remains disconnected and replay-only. Recovered RUNNING steps remain UNKNOWN and are never automatically replayed. No dispatch or real backend is connected.

## Regression coverage

Synthetic stat fixtures cover reparse ancestors, database leaves, SQLite sidecars, policy-mask rebinding, malformed boolean/null/string/float metadata and the absent-field platform default. No privileged junction is created.

## Validation and limits

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed. This is repeated local metadata admission, not atomic descriptor-relative traversal or hostile-writer protection. No paid service, external compute, Candidate, protected V2 evaluation, frozen contract, UI work or main merge occurred.

PR #8 remains Draft/unmerged. ARK/JARVIS remains NOT_PASSED.
