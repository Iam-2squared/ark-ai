# Run1395 — Memory SQLite stat-policy vector epoch custody on current foundation

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `5628f791177668b3c74b6906208b7b92f504ad59`; parent exact-head CI run `45590765382` was GREEN (6/6) before this child was created.
- Rebased from Draft PR #573 / Run1394, whose original child HEAD `43791dd3d433e49454a84d26ef16cc0fbd308855` had CI run `45588944552` GREEN (6/6). That prior result does not transfer to this rebased head.
- Child branch: `research/run1395-memory-stat-epoch-rebase-20261125`.

## Finding and correction

Memory SQLite path admission retained the imported `stat` module and its `S_ISDIR`, `S_ISLNK`, `S_ISREG` and `S_IFMT` predicates through mutable module aliases. Joint replacement of those aliases and the reparse helper's original alias could make equality checks self-consistent.

An import-time tuple now retains the complete path-policy dependency inventory: the stat module, all four mode predicates, the reparse attribute value and original reparse classifier. The verifier captures that tuple in a keyword-only default and checks the aggregate binding plus each working/original alias before filesystem inspection.

## Regression coverage

- Jointly replace the stat module, all four original predicate aliases and the aggregate epoch; denial must occur before `Path.lstat` or a replacement predicate.
- Repeat the replacement reentrantly from a synthetic `Path.lstat` callback; the post-callback policy check must deny before any replacement predicate.

Only synthetic temporary paths and monkeypatched metadata are used.

## Scope and limits

This is local in-process dependency-identity hardening. It is not atomic `dirfd` custody, protection against hostile concurrent filesystem renames, authenticated storage identity, process isolation, consent, physical erasure or external-action authority. Memory v1 DDL/schema, row/event formats, retention, CAS and public APIs are unchanged. No live personal data, external context source, ToolBackend dispatch, notification, hardware, credentials, paid/external compute, Candidate generation/promotion, protected V2 evaluation, frozen-contract change, main merge or UI/frontend work occurred. PR #8 remains Draft/unmerged; no JARVIS PASS is claimed.
