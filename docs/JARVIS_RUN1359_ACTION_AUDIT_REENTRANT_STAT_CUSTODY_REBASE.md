# ARK Run1359 — ActionAudit reentrant stat-policy custody

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `884bd3df8a6966065d0861677bf50eb63db2f9a9`.
- Child branch: `research/run1359-action-audit-stat-custody-rebase-20261125`.
- Source/test rebase basis HEAD: `abd083ae2c29e4ee1ab0bbed414f2aa3aa1ffbaa`.
- Production file: `src/ark/agency/audit.py`.
- Regression module: `tests/test_action_audit_reentrant_stat_custody_run1359.py`.

## Finding and correction

ActionAudit already pinned the stat module and path predicates at import time, but the production path guard still called live `stat.S_ISDIR`, `stat.S_ISREG`, `stat.S_ISLNK` and `stat.S_IFMT` bindings. It also did not recheck the policy immediately after `Path.lstat` or after metadata access. A reentrant filesystem callback could replace a predicate after the initial guard and before the live predicate call; the reparse metadata accessor was another callback boundary.

The path guard now uses the retained import-time predicates, rechecks the pinned policy after each `lstat`, missing-path branch, metadata read and predicate call, and keeps the one-time sidecar recheck bounded. `_is_reparse_point` reads metadata under the same before/after policy checks and uses the retained symlink classifier.

## Regression coverage

- Each stat predicate and the stat module can be replaced from an `lstat` callback; all are rejected before classification.
- Reentrant `st_mode` and `st_file_attributes` accessors cannot change the policy unnoticed.
- Replacement during missing database and missing sidecar callbacks is rejected.
- A valid existing regular audit path remains admissible.

## Scope and evidence boundary

ActionAudit v1 DDL, event fields, digest/request identity, append/read chronology, path identity, audit-before-action call ordering and public API are unchanged. This remains local pathname preflight, not atomic dirfd custody, a sandbox, independently authenticated audit history, trusted-clock proof, authorization or exactly-once external-effect evidence. No real ToolBackend action is invoked.

Predecessor PR #535 CI [45536671862](https://github.com/Iam-2squared/ark-ai/actions/runs/45536671862) was GREEN only on its historical base and does not transfer. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS or CI PASS is claimed. Synthetic temporary paths and metadata only; no live personal data, paid/external compute, Candidate, protected V2 evaluation, credentials, hardware, destructive operation, frozen-contract change, main merge or UI work occurred. PR #5 and PR #8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
