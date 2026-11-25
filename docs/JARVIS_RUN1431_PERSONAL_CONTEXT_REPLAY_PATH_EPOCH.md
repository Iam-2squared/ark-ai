# Run1431 — Personal Context replay path-policy epoch on latest foundation

## Exact basis

- Parent Draft PR #8 branch: `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `c6ee53c5e5671b926b7625da7a7b5dfdd41ae7d3`.
- Rebased from Draft PR #611, branch `research/run1422-context-replay-path-epoch-20261126`, exact prior child HEAD `557f791082180d256f076809b884945f923c0869`.
- Parent source blob before reapplication: `5d2bef090aaec326296a746b8b9215696007df5d`; identical to the source base used by the prior child.
- Source: `src/ark/personal_context_replay_ledger.py`; regression module: `tests/test_context_replay_stat_policy_epoch_run1400.py`.

## Change

Pins the original `os.fsencode` and stat module/predicate inventory, maximum database-path budget, Windows reparse attribute, and reparse classifier in one import-time policy epoch captured by a keyword-only verifier default. The verifier rejects module/alias/epoch substitution before path inspection. `_check_path` uses retained classifiers and rechecks policy across encoding, ancestor/database/sidecar `lstat`, metadata access, and path construction. Reparse-point ancestors, database leaves, and SQLite sidecars are denied before SQLite access.

## Regression coverage

- Joint stat/module/predicate/reparse-helper/epoch replacement is rejected before `Path.lstat`.
- Reentrant ancestor `lstat` replacement is rejected before reading `st_mode`.
- Synthetic reparse-point metadata is rejected for ancestor, database leaf, and SQLite sidecar.
- A reentrant `st_file_attributes` accessor cannot replace policy and return a safe-looking value.

## Scope and evidence limits

Personal Context replay DDL, row format, hash-chain domain, request binding, CAS reservation, retention, and public APIs are unchanged. The ledger remains hash-only and denial-only; this does not prove consent, revocation freshness, disclosure permission, trusted time, independent custody, physical erasure, or exactly-once external effects. Repeated pathname checks are not atomic `dirfd` custody or protection against hostile concurrent filesystem renames.

No live personal data, external context, real dispatch, credentials, hardware, paid/external compute, Candidate generation/promotion, protected V2 evaluation, frozen-contract change, main write/merge, or UI/frontend work occurred. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no production-readiness or ARK/JARVIS PASS is claimed.
