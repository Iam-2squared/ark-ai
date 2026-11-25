# V3 Run1369 — Evidence path stat-policy custody

## Exact basis

- Parent: gated Draft PR #5, branch `research/v3-learning-evaluation`.
- Exact parent work-basis HEAD: `dea011674634d83cf5dba21c5149a885704475dc`.
- Source: `src/ark/learning/training_cli.py`.
- Regression: `tests/v3/test_preflight_report_stat_policy_custody_run1369.py`.

## Finding and change

The V3 evidence reader and preflight-report writer already reject symlinks/reparse points, compare path/descriptor epochs, and bound bytes. Their shared predicates still read mutable `stat` module functions and a mutable reparse mask. A replaced predicate or reentrant `lstat`/metadata accessor could therefore change the path classification during admission.

The change pins the original stat module, directory/regular/symlink classifiers, and reparse-point mask; checks the guard's own identity through an import-original alias; and rechecks after filesystem and metadata callbacks. The report writer uses the retained directory classifier. Existing byte budgets, JSON schema, authorization scope and report format remain unchanged.

## Validation and blocker

- Existing PR #5 exact-head CI run [45542943745](https://github.com/Iam-2squared/ark-ai/actions/runs/45542943745) is **FAIL** at pytest collection: three inherited JARVIS tests import `ark.agency` / `ark.personal_context_offline_preview`, which are not present on `main`. Ruff passed. The core modules remain isolated on Draft PR #8; no main merge or test removal is authorized.
- Fresh exact-head CI for this child is still required; the same base-branch collection blocker is expected. No PASS is claimed.

## Evidence boundary

Synthetic temporary files and metadata only. No torch import, model/tokenizer load, GPU query, preflight backend, training, Candidate creation/promotion, protected V2 evaluation, paid/external compute, credentials, hardware, destructive action, frozen-contract change, main merge or UI work. PR #5 and PR #8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
