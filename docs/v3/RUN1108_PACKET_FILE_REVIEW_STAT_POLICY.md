# Run1108 — V3 detached authorization-packet reader stat-policy custody

## Exact basis

- Parent: gated Draft PR #5, `research/v3-learning-evaluation`.
- Exact parent HEAD: `50b97812dd7eb4bcf3ffb816fb543185cf266e3d`.
- Child branch: `research/run1108-v3-packet-file-review-stat-policy`.
- Production source: `src/ark/learning/authorization_packet_file_review.py`.
- Regression suite: `tests/v3/test_authorization_packet_file_review_stat_policy_run1108.py`.

## Finding

The detached, read-only authorization-packet file reviewer checked the Windows reparse mask, but used live `stat.S_ISREG` and `stat.S_ISLNK` classifiers. Reentrant `Path.lstat`, metadata, `fstat`, and path callbacks could replace those classifiers while the reader was deciding whether packet bytes were safe to open or read. A malformed present `st_file_attributes` value was also silently treated as non-reparse metadata.

## Change

- Pin the import-original `stat` module, regular-file and symlink predicates, and reparse-point mask.
- Recheck that policy after `Path.lstat`, `st_mode`, `st_file_attributes`, link-count and size accessors, `fstat`, file reads, and path re-observation.
- Classify with captured predicates and reject malformed present reparse metadata.
- Preserve the bounded packet byte limit, double-read/file-epoch comparison, hash binding, canonical JSON validation and denial-only witness semantics.

## Synthetic regression coverage

Nine parametrized/synthetic cases cover module and predicate substitution before path inspection, reentrant metadata callbacks, replacement during `lstat` and `fstat`, malformed reparse attributes, and the absent-platform-attribute default. Temporary marker files and synthetic metadata only; no model, Candidate, private data, GPU, network, external action or protected scorer is opened.

## Limits and evidence

This is local Python dependency-identity and pathname metadata admission. It is not atomic directory-handle custody, a sandbox, authenticated provenance, trusted time, human approval, billing evidence, consent or external execution authority.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed. V3 Contract 1 and its hash, Candidate gates, protected V2 evaluation and all frozen V1/V2/Local UI/Launcher evidence remain unchanged. PR #5 remains OPEN/DRAFT/UNMERGED. No paid/external compute, real Candidate adapter/weights, promotion, UI/frontend work, credentials, physical hardware, destructive operation or main merge is involved.

**ARK/JARVIS remains NOT_PASSED.**
