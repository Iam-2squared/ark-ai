# Run1056 — Personal Context replay-ledger reparse admission rebase

## Exact work basis

- Parent branch: `research/jarvis-foundations`.
- Exact parent HEAD: `b973d9e4e5d4ecdd9912a92274622d07ab23748f` (after Run1055 Memory SQLite reparse admission integration).
- Child branch: `research/run1056-personal-context-reparse-rebase`.
- Source: `src/ark/personal_context_replay_ledger.py`.
- Regression: `tests/test_personal_context_replay_reparse_path_run1055.py`.

## Finding and change

The synthetic Personal Context replay-denial ledger rejected POSIX symlinks, non-directory ancestors, hardlinked database files and unsafe SQLite sidecars, but did not classify Windows `FILE_ATTRIBUTE_REPARSE_POINT`. This rebase preserves the exact source change: pins the import-time reparse mask, rejects policy rebinding before filesystem inspection, checks ancestors/database leaf/SQLite sidecars, and fails closed on malformed present metadata while preserving the absent-field platform default.

The hash-only row format, replay-chain schema, path byte budget and denial-only authority flags remain unchanged.

## Regression coverage

Synthetic tests cover policy rebinding, malformed boolean/null/string/float metadata, the absent-field default, reparse ancestors before leaf inspection, database leaves and SQLite sidecars. No privileged junction is created.

## Validation and limits

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed. This is repeated pathname metadata admission, not atomic descriptor-relative custody or hostile-writer protection. No live personal data, disclosure, consent, trusted time, independent custody, ToolBackend, external effect, paid service, external compute, Candidate, protected V2 evaluation, frozen-contract change, UI work or main merge occurred.

PR #8 remains Draft/unmerged. ARK/JARVIS remains NOT_PASSED.
