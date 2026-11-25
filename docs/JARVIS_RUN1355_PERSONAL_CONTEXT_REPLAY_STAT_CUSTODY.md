# ARK Run1355 — Personal Context replay-ledger stat-policy custody

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `8c969bbd2dc83c800b7bad998fd8e480aec941e7`.
- Child branch: `research/run1355-personal-context-replay-stat-custody-20261125`.
- Implementation and regression head before this evidence note: `f1e6c8331102294e665b89bd7ce3c70a9e4b7aee`.
- Production file: `src/ark/personal_context_replay_ledger.py`.
- Regression module: `tests/test_personal_context_replay_stat_custody_run1355.py`.

## Finding and correction

The disconnected Personal Context replay ledger used live `stat.S_ISDIR`, `stat.S_ISLNK` and `stat.S_ISREG` bindings during ancestor, database-leaf and SQLite-sidecar checks. Its replay-protocol guard pinned SQLite, hashing, JSON, regular expressions and protocol constants, but not the filesystem classifiers. A replaced predicate could misclassify a path; a reentrant `lstat` callback could replace a predicate after the initial protocol check.

The replay-protocol guard now pins the import-time stat module and exact predicates. Path admission classifies with the retained callables and rechecks the complete protocol after metadata callbacks, predicate calls and missing database/sidecar outcomes. Existing fail-closed creation and orphan-sidecar behavior is preserved.

## Regression coverage

- Preinstalled replacement of each stat predicate is rejected before `Path.lstat`.
- Stat module replacement is rejected before `Path.lstat`.
- Predicate/module replacement during ancestor `lstat` is rejected before classification.
- Replacement during missing database and missing sidecar callbacks is rejected.
- A valid existing local path remains admissible.

## Scope and evidence boundary

The replay table schema/DDL, hash-chain format, request-binding contract, CAS/reservation semantics, retention and denial-only receipt behavior are unchanged. This remains a synthetic local hash-only replay ledger; it does not establish consent, revocation freshness, disclosure permission, trusted time, independent custody, dispatch or exactly-once external effects. Path checks remain repeated `lstat` preflights, not atomic directory-handle custody or a sandbox.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS or CI PASS is claimed. No live personal data, paid/external compute, Candidate, protected V2 evaluation, credentials, hardware, destructive operation, frozen-contract change, main merge or UI work occurred. PR #5 and PR #8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
