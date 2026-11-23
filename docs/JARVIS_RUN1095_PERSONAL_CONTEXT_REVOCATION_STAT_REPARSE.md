# Run1095 — Personal Context revocation stat/reparse custody

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`
- Work-basis HEAD: `d7de07d4d5d1239d3748b43d590dd102a2547c1c`
- Child branch: `research/run1095-personal-context-revocation-stat-reparse`
- Production source: `src/ark/personal_context_revocation_review.py`
- Regression tests: `tests/test_revocation_stat_reparse_custody_run1095.py`

## Change

- Pins the imported `stat` module, its `S_ISDIR`, `S_ISLNK`, and `S_ISREG` predicates, and the Windows `FILE_ATTRIBUTE_REPARSE_POINT` mask.
- Rechecks the classification policy around path metadata callbacks and rejects malformed mode/link/reparse metadata.
- Applies the same non-reparse regular-file classification to the revocation database and SQLite sidecars, and non-reparse directory classification to every ancestor.
- Preserves the existing lexical traversal, UTF-8/native path budgets, symlink/hardlink denial, orphan-sidecar handling, and create-forbidden recovery behavior.
- Adds six synthetic tests for pre-access and callback-time predicate replacement, reparse-mask replacement, and reparse ancestor/source/sidecar rejection.

## Scope and limits

This is a local fail-closed pathname preflight only. It does not provide atomic directory-handle custody, authenticate filesystem ownership or consent, establish trusted time, make separate Memory/revocation SQLite files atomic, or prove secure erasure. The frozen Memory v1 schema/API and Local UI/Launcher/V1/V2 evidence are unchanged. No live personal data, external service, paid compute, Candidate generation, protected V2 evaluation, UI/frontend work, or main merge is involved.

## Validation

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS or CI GREEN is claimed here.