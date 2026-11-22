# Run1109 — Planner journal reentrant stat-policy custody rebase

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent HEAD: `62047e185d4f8b8fef9a94b3f6441ff1b42c307d`.
- Reapplied from Draft PR #250 exact child HEAD: `98e865fa4a3ad749e66da6859fce986ce89ae0ff`.
- New child branch: `research/run1109-planner-journal-stat-reentrant-rebase`.
- Source: `src/ark/agency/planner_journal_review.py`.
- Synthetic regression suite: `tests/test_planner_journal_stat_predicate_custody_run1109.py`.

## Finding and change

The replay-only Planner journal path preflight now pins the import-original stat module and `S_ISDIR` / `S_ISLNK` / `S_ISREG` classifiers, rechecking policy after ancestor/leaf `lstat`, missing-leaf handling, `Path.exists`, metadata accessors and sidecar re-observation. Classification uses captured originals.

The journal schema, hash chain, transition policy and ambiguous/UNKNOWN treatment of recovered RUNNING steps are unchanged. No automatic retry, dispatch, or external execution authority is introduced.

## Synthetic regression coverage

Tests cover pre-access and callback-time module/predicate substitution, missing-leaf callbacks, and reentrant Windows reparse metadata accessors. Temporary paths and monkeypatched callbacks only; no private journal or external action is opened.

## Limits and evidence

This is local dependency-identity and lexical pathname preflight hardening, not atomic directory-handle custody, a sandbox, independent provenance, trusted time, consent, power-loss durability or exactly-once external effects. No local pytest/Ruff PASS is claimed. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; prior CI on another parent/head does not transfer.

No paid/external compute, Candidate, protected V2 evaluation, frozen-contract change, credentials, physical hardware, UI/frontend work, destructive operation or main merge. PR #8 remains Draft/unmerged. **ARK/JARVIS remains NOT_PASSED.**
