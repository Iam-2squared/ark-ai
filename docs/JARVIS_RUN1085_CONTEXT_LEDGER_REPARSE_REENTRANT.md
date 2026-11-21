# Run1085 — Personal Context replay-ledger path custody

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent HEAD: `916aae6c6578086fee5e83c77c23375712676c90`.
- Source: `src/ark/personal_context_replay_ledger.py`.
- Existing path coverage: `tests/test_context_replay_sidecar_custody_run793.py` and `tests/test_context_replay_sqlite_preaccess_run859.py`.
- New child branch: `research/run1085-context-ledger-reparse-reentrant`.

## Finding and change

The hash-only Personal Context replay ledger bounded paths and rejected POSIX symlinks, hardlinks and unsafe SQLite sidecars, but did not pin the stat module/predicates or inspect Windows `FILE_ATTRIBUTE_REPARSE_POINT`. Reentrant `Path.lstat` and metadata accessors could also change classification policy after the initial path check.

This child pins import-original stat/encoding dependencies, rechecks them after each filesystem/metadata callback, captures original classifiers, and rejects Windows reparse points on ancestors, the database leaf and SQLite sidecars. Hash-only request rows, ledger schema, replay protocol, and all denial-only authority properties remain unchanged.

## Synthetic regression coverage

Adds pre-access and callback-time stat substitution tests, missing-leaf and metadata-accessor reentrancy tests, plus synthetic Windows reparse metadata for ancestor, main file and sidecar paths. Tests call the path checker directly and do not open or create a private ledger.

## Limits and evidence

This is local pathname admission, not atomic directory-handle custody, a sandbox, authenticated consent, trusted time, independent storage provenance, or proof of exactly-once effects. No local pytest/Ruff PASS is claimed; fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required.

No paid/external compute, Candidate, protected V2 evaluation, frozen-contract change, UI/frontend work, credentials, physical hardware action, or main merge is involved.

**ARK/JARVIS remains NOT_PASSED.**
