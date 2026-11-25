# ARK Run1360 — Personal Context replay-ledger stat-policy custody

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `884bd3df8a6966065d0861677bf50eb63db2f9a9`.
- Child branch: `research/run1360-personal-context-replay-reparse-custody-rebase-20261125`.
- Source/test rebase basis HEAD: `782f6dd7fe5619cf83c6f0965e0eec5818211bfb`.
- Production file: `src/ark/personal_context_replay_ledger.py`.
- Regression module: `tests/test_personal_context_replay_stat_custody_run1360.py`.

## Finding and correction

The disconnected Personal Context replay ledger used live `stat.S_ISDIR`, `stat.S_ISLNK` and `stat.S_ISREG` bindings during ancestor, database-leaf and SQLite-sidecar checks. Its replay-protocol guard pinned SQLite, hashing, JSON, regular expressions and protocol constants, but not the filesystem classifiers. A replaced predicate could misclassify a path; a reentrant `lstat` callback could replace a predicate after the initial protocol check.

The replay-protocol guard now pins the import-time stat module, exact predicates and Windows reparse-point attribute mask. Path admission classifies with retained callables, rejects POSIX symlinks and Windows reparse-point metadata for ancestors, the database and SQLite sidecars, and rechecks the complete protocol after metadata callbacks, predicate calls and missing database/sidecar outcomes. Existing fail-closed creation and orphan-sidecar behavior is preserved.

## Regression coverage

- Preinstalled replacement of each stat predicate is rejected before `Path.lstat`.
- Stat module replacement is rejected before `Path.lstat`.
- Predicate/module replacement during ancestor `lstat` is rejected before classification.
- Replacement during missing database and missing sidecar callbacks is rejected.
- Windows reparse-point metadata on an ancestor, database or SQLite sidecar is rejected.
- Reentrant metadata accessors and reparse-mask replacement are rejected before unsafe path admission.
- A valid existing local path remains admissible.

## Scope and evidence boundary

The replay table schema/DDL, hash-chain format, request-binding contract, CAS/reservation semantics, retention and denial-only receipt behavior are unchanged. This remains a synthetic local hash-only replay ledger; it does not establish consent, revocation freshness, disclosure permission, trusted time, independent custody, dispatch or exactly-once external effects. Path checks remain repeated `lstat` preflights, not atomic directory-handle custody or a sandbox.

Predecessor PR #534 CI [45536363929](https://github.com/Iam-2squared/ark-ai/actions/runs/45536363929) was GREEN only on its historical base and does not transfer. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS or CI PASS is claimed. No live personal data, paid/external compute, Candidate, protected V2 evaluation, credentials, hardware, destructive operation, frozen-contract change, main merge or UI work occurred. PR #5 and PR #8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
