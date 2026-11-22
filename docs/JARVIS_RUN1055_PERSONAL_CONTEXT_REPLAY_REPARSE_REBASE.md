# Run1055 — Personal Context replay ledger reparse admission rebase

## Exact work basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent HEAD: `ae6eb0a2ec2fb1db23ac3ae2fccbb03ab24d34b9`.
- Child branch: `research/run1055-personal-context-reparse-rebase`.
- Source: `src/ark/personal_context_replay_ledger.py`.
- Regression: `tests/test_personal_context_replay_reparse_path_run1055.py`.

## Finding and change

The synthetic Personal Context replay-denial ledger rejected POSIX symlinks, non-directory ancestors, hardlinked database files and unsafe SQLite sidecars, but did not classify Windows `FILE_ATTRIBUTE_REPARSE_POINT`. A junction/reparse ancestor, database leaf or sidecar could retain ordinary mode bits and pass the existing symlink-only checks.

This rebase onto the current PR #8 head:
- Pins the import-time reparse-point attribute mask as part of the replay protocol identity.
- Rejects policy-mask rebinding before filesystem inspection.
- Detects POSIX symlinks and Windows reparse-point attributes on every ancestor, the database leaf and SQLite sidecars.
- Fails closed when a present `st_file_attributes` carrier is not an exact integer; preserves the absent-field default on platforms without the Windows field.
- Preserves the hash-only row format, replay-chain schema, path byte budget and denial-only authority flags.

## Regression coverage

Synthetic tests cover policy rebinding before `lstat`, malformed metadata carriers, the absent-field platform default, a reparse ancestor before leaf inspection, a reparse database leaf and a reparse WAL sidecar. No privileged Windows junction is created and no live personal data is used.

## Limits and frozen boundaries

This is repeated local metadata admission, not atomic descriptor-relative traversal, independent custody, authenticated consent, trusted time, disclosure permission or exactly-once external action evidence. The ledger remains a synthetic hash-only replay-denial fixture. No real ToolBackend, dispatch, notification, external effect, paid service, external compute, credential, Candidate, protected V2 evaluation, frozen contract, UI work or main merge is involved.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed. PR #8 remains Draft/unmerged; ARK/JARVIS remains NOT_PASSED.
