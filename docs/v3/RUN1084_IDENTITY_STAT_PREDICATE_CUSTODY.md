# Run1084 — V3 identity stat predicate custody

## Exact basis

- Parent: gated Draft PR #5, branch `research/v3-learning-evaluation`.
- Exact parent HEAD: `2ddc32a69dd32541497373ac76be2c1db332f88f`.
- Child branch: `research/run1084-v3-identity-stat-predicate-custody`.
- Prior identity reparse-mask guard: Run1051, parent basis `034c756345b218ce41770ffccad7390a17ec018b`.
- Source modules: `src/ark/learning/identity.py` and `src/ark/learning/identity_artifact_verify.py`.
- Regression: `tests/v3/test_identity_stat_predicate_custody_run1084.py`.

## Finding

The V3 local identity manifest pinned its Windows reparse-point mask and rejected malformed present metadata, but still called live `stat.S_ISDIR`, `stat.S_ISREG` and `stat.S_ISLNK` predicates. The local identity-artifact verifier likewise relied on live `S_ISREG` and pathlib's `S_ISLNK`. Rebinding the imported module or a predicate could alter path classification after the earlier policy check.

## Change

- Pin the import-original `stat` module and the exact mode predicates used by each verifier.
- Reject module/predicate replacement before filesystem inspection.
- Recheck policy after mode/attribute metadata reads and after pathlib symlink checks.
- Use captured predicates for regular-file, directory and reparse classification in the identity manifest.
- Pin both regular-file and symlink predicates in the identity-artifact verifier, including descriptor and post-read path checks.
- Add twelve synthetic regressions for module/predicate substitution and reentrant metadata callbacks.

## Limits and frozen boundaries

This is local filesystem metadata hardening, not atomic descriptor-relative traversal, immutable filesystem custody, authenticated provenance, or protection against a hostile kernel/concurrent writer. Tests use only disposable synthetic temporary files. No real model snapshot was materialized, opened or hashed; no converter, quantizer, model load, GPU, network service, Candidate generation, training, protected V2 evaluation, or automatic promotion was invoked.

V3 Contract 1 and its hash remain unchanged. PR #5 remains OPEN/DRAFT/UNMERGED. PR #9 and all UI/frontend work remain paused and untouched. No paid service, credentials, destructive operation, or main merge is involved.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed. V3 remains NOT_PASSED.
