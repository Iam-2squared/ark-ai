# Run1394 — Memory SQLite stat-policy vector epoch custody

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `5213af024a080c63062c5eb18e51eff7c0d5a39d`.
- Child branch: `research/run1394-memory-sqlite-stat-vector-epoch-custody-20261125`.

## Finding

Memory SQLite path admission retained the imported `stat` module and
`S_ISDIR`, `S_ISLNK`, `S_ISREG` and `S_IFMT` predicates through mutable
module aliases. Its verifier compared the working module with
`_ORIGINAL_STAT` and each live predicate with a mutable original alias.
Jointly replacing those bindings and the reparse helper's original alias could
make the equality checks self-consistent.

## Correction

An import-time tuple now retains the complete path-policy dependency
inventory: the stat module, all four mode predicates, the reparse attribute
value and the original reparse classifier. The path-policy verifier captures
that tuple in a keyword-only default and checks the aggregate binding and each
working/original alias before filesystem inspection. Existing path, sidecar,
metadata, store-identity and SQLite behavior is unchanged.

## Regression coverage

- Jointly replace the stat module, all four original predicate aliases and
  the aggregate epoch; denial must occur before `Path.lstat` or a replacement
  predicate.
- Repeat the replacement reentrantly from a synthetic `Path.lstat` callback;
  the post-callback policy check must deny before any replacement predicate.

Only synthetic temporary paths and monkeypatched metadata are used.

## Scope and limits

This is local in-process dependency-identity hardening. It is not atomic
`dirfd` custody, protection against hostile concurrent filesystem renames,
authenticated storage identity, process isolation, consent, physical erasure,
or external-action authority. Memory v1 DDL/schema, row/event formats,
retention, CAS and public APIs are unchanged. No live personal data, external
context source, ToolBackend dispatch, notification, hardware, credentials,
paid/external compute, Candidate generation/promotion, protected V2
evaluation, frozen-contract change, main merge or UI/frontend work occurred.
PR #8 remains Draft/unmerged; no JARVIS PASS is claimed.
