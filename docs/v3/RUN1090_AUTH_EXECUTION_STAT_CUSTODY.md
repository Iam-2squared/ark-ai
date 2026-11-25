# Run1090 — V3 authorization and execution snapshot stat-policy custody

## Exact basis

- Parent: gated Draft PR #5, `research/v3-learning-evaluation`.
- Exact parent HEAD: `2ddc32a69dd32541497373ac76be2c1db332f88f`.
- Child branch: `research/run1090-v3-auth-execution-stat-custody`.
- Authorization source update: `0f66c922877e9906fcc644db0d02a89ccda07272`.
- Execution source update: `5555778d55dca3df7e74a8fc27c4759cd52bb139`.
- Regression module: `tests/v3/test_authorization_execution_stat_predicate_custody_run1090.py`, commit `fc6e5b588e629e67974e9b6c44ec636059a6e7b2`.

## Finding

The V3 authorization-packet writer and execution-snapshot loader still called live `stat.S_ISREG` / `stat.S_ISLNK` predicates. A replaced stat module or predicate, including replacement from a reentrant metadata, path-open or JSON-decoder callback, could change the local path classification policy while these functions were running.

## Change

- Pin the import-original `stat` module, regular-file and symlink predicates, and Windows reparse-point mask in both modules.
- Validate exact integer mode and reparse metadata, rechecking the original policy after metadata accessors.
- Reject reparse-point snapshot leaves as well as non-regular files.
- Recheck authorization path policy after parent/symlink inspection, after exclusive create, before writing packet bytes, and during post-write readback.
- Recheck execution policy after PathLike conversion, lstat, open, fstat, file read and JSON decoding. The initial open callback is checked before snapshot bytes are read.
- Add 13 synthetic regressions for module/predicate substitution and reentrant metadata, open and decoder callbacks.

## Validation and limits

No local pytest/Ruff result is claimed. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required after opening the Draft child PR. Tests use synthetic temporary files only; no model snapshot, Candidate, converter, quantizer, training, GPU, network, paid service, external compute, or protected scorer is opened.

This is local metadata/path-policy hardening, not atomic descriptor-relative traversal, authenticated provenance, trusted time, provider billing evidence, consent, external execution authority, or immutable filesystem custody. V3 Contract 1 and its hash are unchanged. PR #5 remains OPEN/DRAFT/UNMERGED; no protected V2 evaluation or Candidate promotion is opened. PR #9 and all UI/frontend work remain paused and untouched. ARK/JARVIS remains NOT_PASSED.
