# Run1085 — Planner journal reentrant stat-policy custody

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent HEAD: `916aae6c6578086fee5e83c77c23375712676c90`.
- Superseded older rebase: Draft PR #203, `research/run1075-planner-stat-predicate-rebase`, based on `663112db8eed74148daedc6dd78e217302c82b15`.
- New child branch: `research/run1085-planner-journal-stat-reentrant`.

## Change

Reapply the previously reviewed Planner journal stat-module and `S_ISDIR` / `S_ISLNK` / `S_ISREG` identity pins to the current foundation, then close a reentrant gap: the journal path preflight now rechecks the pinned policy after `Path.lstat`, missing-leaf handling, `Path.exists`, and metadata field access. Classification uses captured import-original predicates rather than looking up live module attributes after callbacks.

The replay-only journal schema, hash chain, transition semantics, and UNKNOWN treatment of recovered RUNNING steps are unchanged. No dispatch or automatic replay authority is introduced.

## Synthetic regression coverage

The new test module carries forward pre-access module/predicate substitution checks and adds callback-time predicate/module substitution, missing-leaf callback, and Windows reparse-metadata accessor cases. Tests use temporary paths and monkeypatched in-process callbacks only.

## Limits and evidence

This is local Python dependency-identity and pathname-preflight hardening. It is not atomic directory-handle custody, a sandbox, independent provenance, trusted time, consent, power-loss durability, or exactly-once external effects. No local pytest/Ruff PASS is claimed. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required.

No paid service, external compute, Candidate generation, protected V2 evaluation, frozen-contract change, UI/frontend work, credentials, physical hardware action, or main merge is involved.

**ARK/JARVIS remains NOT_PASSED.**
