# Run1054 — Personal Context replay ledger Windows reparse-point admission

## Exact work basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent HEAD: `a48c0464b75a5355606f2369551f79a9012a95ea`.
- Child branch: `research/run1054-personal-context-replay-reparse-path`.
- Source: `src/ark/personal_context_replay_ledger.py`.
- Regression: `tests/test_personal_context_replay_reparse_path_run1054.py`.

## Finding

The synthetic Personal Context replay-denial ledger already rejected POSIX symlinks, non-directory ancestors, hardlinked database files and unsafe SQLite sidecars. It did not classify Windows `FILE_ATTRIBUTE_REPARSE_POINT`, so a junction/reparse ancestor, database leaf or sidecar could retain ordinary mode bits and pass the existing symlink-only checks.

## Change

- Pin the import-time reparse-point attribute mask as part of the replay protocol identity.
- Reject policy-mask rebinding before any filesystem inspection.
- Detect POSIX symlinks and Windows reparse-point attributes on every ancestor, the database leaf and SQLite sidecars.
- Fail closed when a present `st_file_attributes` carrier is not an exact integer; preserve the absent-field default on platforms without the Windows field.
- Preserve the hash-only row format, replay-chain schema, path byte budget, and denial-only authority flags.

## Regression coverage

Synthetic tests cover policy rebinding before `lstat`, malformed metadata carriers, the absent-field platform default, a reparse ancestor before leaf inspection, a reparse database leaf and a reparse WAL sidecar. No privileged Windows junction is created and no live personal data is used.

## Limits and frozen boundaries

This is repeated local metadata admission, not atomic descriptor-relative traversal, independent custody, authenticated consent, trusted time, disclosure permission, or exactly-once external action evidence. The ledger remains a synthetic hash-only replay-denial fixture. No real ToolBackend, dispatch, notification, external effect, paid service, external compute, credential, Candidate, protected V2 evaluation, frozen contract, UI work or main merge is involved.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed. PR #8 remains Draft/unmerged; ARK/JARVIS remains NOT_PASSED.
