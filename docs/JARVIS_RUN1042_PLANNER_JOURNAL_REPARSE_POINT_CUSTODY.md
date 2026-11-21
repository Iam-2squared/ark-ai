# Run1042 — Planner journal Windows reparse-point admission

## Exact work basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent HEAD: `812e5d3777376d5903cbbd17dca967f7448d0e11`.
- Child branch: `research/run1042-planner-journal-reparse-point-custody`.
- Source: `src/ark/agency/planner_journal_review.py`.
- Regression: `tests/test_planner_journal_reparse_point_ancestry_run1042.py`.

## Finding

The disconnected Planner journal rejected POSIX symlinks, unsafe ancestors, hardlinked leaves and SQLite sidecars. A Windows directory junction or other reparse-point entry can still report directory mode without `stat.S_ISLNK` being true. The path preflight therefore needed to classify the Windows reparse attribute separately.

## Change

- Pin the import-time `FILE_ATTRIBUTE_REPARSE_POINT` mask and fail closed if the policy value is rebound.
- Reject reparse-point ancestors before journal creation or reopen.
- Reject a reparse-point database leaf before SQLite access.
- Reject reparse-point WAL/SHM/rollback-journal sidecars before SQLite access.
- Preserve existing lexical path, POSIX symlink, regular-file, hardlink and orphan-sidecar checks.

## Regression coverage

Synthetic cross-platform stat fixtures cover a directory-mode reparse ancestor, a regular-file-mode reparse database leaf, a reparse sidecar, and reparse-policy rebinding before any lstat. No privileged junction is created.

## Limits and frozen boundaries

This is repeated local metadata admission, not atomic descriptor-relative traversal, hostile concurrent-writer protection, authenticated journal provenance, or a trusted-clock/dispatch guarantee. The journal remains disconnected and replay-only; recovered RUNNING steps remain UNKNOWN. No real backend, dispatch, automatic replay, frozen contract, V1/V2/Local UI/Launcher evidence, PR #5, PR #9, Candidate, paid service, external compute or main branch is changed.
