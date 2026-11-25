# Run1430 — ActionAudit reparse-policy epoch on latest foundation

## Exact basis

- Parent Draft PR #8 branch: `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `c6ee53c5e5671b926b7625da7a7b5dfdd41ae7d3`.
- Rebased from Draft PR #614, branch `research/run1425-action-audit-reparse-epoch-20261126`, exact prior child HEAD `be8acdc30ee32bdf999fbe621baedac808546f51`.
- Parent source blob before reapplication: `0d861227646eb502904217b1cf2eb09e770ec5e8`; identical to the prior child's source base.
- Source: `src/ark/agency/audit.py`; regression module: `tests/test_action_audit_reparse_vector_epoch_run1399.py`.

## Change

Retains the complete stat/reparse path-policy dependency inventory in one import-time epoch captured by a keyword-only verifier default. The verifier validates the aggregate epoch, stat module, original/live mode predicates, and reparse attribute before filesystem inspection. Reparse metadata is rechecked before reading mode or applying the retained classifier.

## Regression coverage

- Joint replacement of the stat module, predicate aliases, reparse value, and aggregate epoch is rejected before `Path.lstat`.
- A synthetic `st_file_attributes` accessor attempts the same replacement reentrantly; denial occurs before `st_mode` is read or any hostile predicate executes.

## Scope and evidence limits

This is local in-process path-policy identity hardening only—not atomic `dirfd` custody, protection from hostile filesystem renames, authenticated storage identity, process isolation, consent, or physical erasure. ActionAudit v1 DDL/event fields, chronology, hash chain, audit-before-action semantics, and public APIs are unchanged.

No live user data, real dispatch, credentials, hardware, paid/external compute, Candidate generation/promotion, protected V2 evaluation, frozen-contract change, main write/merge, or UI/frontend work occurred. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no production-readiness or ARK/JARVIS PASS is claimed.
