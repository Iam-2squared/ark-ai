# Run1399 — ActionAudit reparse-policy vector epoch custody

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `5628f791177668b3c74b6906208b7b92f504ad59`; parent exact-head CI run `45590765382` was GREEN (6/6) before this child was created.
- Child branch: `research/run1399-action-audit-reparse-vector-epoch-20261125`.
- Existing single-alias regressions in `tests/test_action_audit_stat_predicate_custody_run1072.py` remain unchanged.

## Finding and correction

ActionAudit path admission compared the live `stat` module and its four mode predicates with mutable original aliases. Joint replacement of the module, predicates, reparse attribute and original aliases could make those checks self-consistent. The reparse metadata accessor also had no post-callback policy recheck before reading `st_mode` and applying `S_ISLNK`.

An import-time tuple now retains the complete stat/reparse dependency inventory, captured by a keyword-only verifier default. The verifier checks the aggregate epoch, module identity, all four working/original predicate aliases and the reparse attribute before filesystem inspection. `_is_reparse_point` rechecks after metadata access and before mode access/classification, then uses the retained original symlink predicate and reparse attribute.

## Regression coverage

- Joint replacement of the stat module, all predicate aliases, reparse value and aggregate epoch is denied before `Path.lstat`.
- A synthetic `st_file_attributes` property installs the same replacement reentrantly; denial occurs before `st_mode` is read or any hostile predicate executes.

## Scope and limits

Local in-process path-policy identity hardening only. This is not atomic `dirfd` custody, protection from hostile filesystem renames, authenticated storage identity, process isolation, consent or physical erasure. ActionAudit v1 DDL/event fields, chronology, hash chain, audit-before-action semantics and public APIs are unchanged. No live user data, real dispatch, credentials, hardware, paid/external compute, Candidate generation/promotion, protected V2 evaluation, frozen-contract change, main merge or UI/frontend work occurred. PR #8 remains Draft/unmerged; ARK/JARVIS remains NOT_PASSED.
