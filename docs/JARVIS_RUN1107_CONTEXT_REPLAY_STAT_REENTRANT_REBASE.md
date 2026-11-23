# Run1111 — Rebased Run1107 Personal Context replay-ledger path-policy guards

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent HEAD at branch creation: `22a22aa08001990739e6c1607d7b1b1cd7b0d9a6`.
- Reapplied from predecessor Draft PR #257 exact child HEAD: `c47aa90f14e933229cf03295321b60cafeda92d4` (exact-head CI run 45009601750 was GREEN 6/6 on its old base and does not transfer).
- Rebased from Draft PR #222 exact child HEAD: `f332fe623008ae6ff3b2da856ff80f533a82ba41`.
- Source: `src/ark/personal_context_replay_ledger.py`.
- Existing path coverage: `tests/test_context_replay_sidecar_custody_run793.py` and `tests/test_context_replay_sqlite_preaccess_run859.py`.
- Child branch: `research/run1111-personal-context-replay-rebase`.

## Finding and change

The hash-only Personal Context replay ledger bounded paths and rejected POSIX symlinks, hardlinks and unsafe SQLite sidecars, but did not pin the stat module/predicates or inspect Windows `FILE_ATTRIBUTE_REPARSE_POINT`. Reentrant `Path.lstat` and metadata accessors could also change classification policy after the initial path check.

This rebase pins import-original stat/encoding dependencies, rechecks them after filesystem and metadata callbacks, captures original classifiers, and rejects Windows reparse points on ancestors, the database leaf and SQLite sidecars. Hash-only request rows, ledger schema, replay protocol, and all denial-only authority properties remain unchanged.

## Synthetic regression coverage

Carries forward pre-access and callback-time stat substitution tests, missing-leaf and metadata-accessor reentrancy tests, and synthetic Windows reparse metadata for ancestor, main file and sidecar paths. Adds main-file and sidecar link-count accessor substitutions. Tests call the path checker directly and use temporary marker files only; they do not open or create a private ledger.

## Limits and evidence

This is local pathname admission, not atomic directory-handle custody, a sandbox, authenticated consent, trusted time, independent storage provenance, or proof of exactly-once effects.

No local pytest/Ruff PASS is claimed. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. The prior PR #222 CI, if any, is on a different parent/head and does not transfer.

No paid/external compute, paid API/service, Candidate, protected V2 evaluation, frozen-contract change, UI/frontend work, credential/account connection, physical hardware action, destructive operation or main merge is involved.

**ARK/JARVIS remains NOT_PASSED.**


## Run1111 rebase evidence

The predecessor child PR #257 exact head `c47aa90f14e933229cf03295321b60cafeda92d4` passed Windows/Linux × Python 3.11–3.13 CI run [45009601750](https://github.com/Iam-2squared/ark-ai/actions/runs/45009601750), 6/6. That result does not transfer to this rebased branch; fresh exact-head CI is required.