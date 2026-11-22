# Run1055 — Planner journal Windows reparse-point admission rebase

## Exact work basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent HEAD: `ae6eb0a2ec2fb1db23ac3ae2fccbb03ab24d34b9`.
- Child branch: `research/run1055-planner-journal-reparse-rebase`.
- Source: `src/ark/agency/planner_journal_review.py`.
- Regression: `tests/test_planner_journal_reparse_point_ancestry_run1055.py`.

## Finding and change

The disconnected replay-only Planner journal rejected POSIX symlinks, unsafe ancestors, hardlinked leaves and SQLite sidecars, but Windows junctions/reparse points can retain ordinary directory/file mode bits. The package pins the Windows reparse mask and rejects reparse-point ancestors, database leaves and WAL/SHM/rollback-journal sidecars before SQLite use.

The rebase also closes a malformed-metadata gap: a present non-exact-integer `st_file_attributes` value now fails closed rather than being treated as if the reparse bit were absent. The database leaf is inspected with `lstat` directly, avoiding a preceding `exists()` follow through a reparse target.

## Regression coverage

Synthetic stat fixtures cover reparse ancestors, database leaves, SQLite sidecars, policy-mask rebinding, malformed boolean/null/string/float metadata and the absent-field platform default. The malformed-ancestor case proves the leaf is not inspected after bad ancestor metadata. No privileged junction is created.

## Limits and frozen boundaries

This is repeated local metadata admission, not atomic descriptor-relative traversal, hostile concurrent-writer protection, authenticated journal provenance or trusted-clock/dispatch evidence. The journal remains disconnected and replay-only; recovered RUNNING steps remain UNKNOWN. No real backend, dispatch, automatic replay, frozen contract, V1/V2/Local UI/Launcher evidence, PR #5, PR #9, Candidate, paid service, external compute or main merge is involved.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed. PR #8 remains Draft/unmerged; ARK/JARVIS remains NOT_PASSED.
