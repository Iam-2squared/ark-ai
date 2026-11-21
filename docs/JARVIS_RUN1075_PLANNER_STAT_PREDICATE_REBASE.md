# Run1075 — Planner journal stat-predicate custody rebase

## Exact basis

- Original reviewed child: Draft PR #202, `research/run1074-planner-stat-predicate-custody`, exact child HEAD `37696654fe8d9fc6ec71bde39fb2911ea2b425fe`.
- Original parent at review: `2e408656ae0661626e6bc3fb234006819ef2ccfc`.
- Rebase parent: Draft PR #8, `research/jarvis-foundations`, exact HEAD `663112db8eed74148daedc6dd78e217302c82b15`.
- Rebase branch: `research/run1075-planner-stat-predicate-rebase`.

## Change

Reapply the isolated Planner journal path-admission identity guard to the latest foundation. The import-original `stat` module and the exact `S_ISDIR`, `S_ISLNK`, and `S_ISREG` predicates are pinned before `lstat`, directory creation, or SQLite access. The disconnected journal remains replay-only; recovered RUNNING steps remain UNKNOWN. Planner journal schema, hash chain, and transition policy are unchanged.

## Regression coverage

The original child contains four synthetic regressions for predicate/module substitution. Each requires the existing fail-closed diagnostic before filesystem inspection. The original exact child-head CI run `44926673951` completed successfully (6/6); this rebase requires a new exact-head CI run and does not transfer that result.

## Limits

This is local in-process dependency-identity hardening, not atomic directory-handle custody, a sandbox, dispatch authority, automatic replay, trusted time, consent, independent custody, power-loss durability, or exactly-once external effects. No local pytest/Ruff PASS is claimed. No paid service, external compute, Candidate, protected V2 evaluation, frozen-contract change, UI, credentials, physical hardware, or main merge is involved.

**ARK/JARVIS remains NOT_PASSED.**
