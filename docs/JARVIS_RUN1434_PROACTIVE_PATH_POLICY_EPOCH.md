# Run1434 — Proactive SQLite path-policy epoch on latest foundation

## Exact basis

- Parent Draft PR #8 branch: `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `c6ee53c5e5671b926b7625da7a7b5dfdd41ae7d3`.
- Rebased from Draft PR #610, branch `research/run1421-proactive-path-epoch-20261126`, exact prior child HEAD `78a3e677eecc17e90eb24063458cc21cfb33a4a0`.
- Parent source blob before reapplication: `eb192fac2b7642af32b91c0636a5118cefbb3dbe`; identical to the prior child's source base.
- Existing transient-journal test blob before fixture correction: `5d907b9d49cb877a95e40eca37726271bc8b2571`; identical to the prior child's base.
- Source: `src/ark/proactive_synthetic_review.py`; new regression module: `tests/test_proactive_path_policy_epoch_run1401.py`; corrected metadata fixture: `tests/test_proactive_transient_journal_preflight_run801.py`.

## Change

Pins the original `os.fsencode`, stat module/mode predicates, path budget, Windows reparse attribute/classifier, and exact SQLite sidecar suffix tuple in one import-time policy epoch. It uses retained predicates and rechecks the epoch after `lstat`, metadata access, path encoding, and sidecar construction. Reparse-point ancestors, database files, and sidecars are denied before SQLite open. The bounded one-time recheck for an already-unlinked regular sidecar is preserved.

## Regression coverage

- Joint stat/reparse/sidecar-policy replacement is rejected before `Path.lstat`.
- Equal-valued but newly allocated sidecar suffix tuples are rejected.
- Reentrant `lstat` replacement is rejected before `st_mode` access.
- Synthetic reparse-point parent, database, and sidecar metadata are rejected.
- A reentrant `st_file_attributes` accessor cannot replace policy.
- The already-unlinked regular-sidecar path receives only its existing single bounded recheck.
- Healthy synthetic trigger and proactive state ledgers remain usable and deny-only.
- The transient-journal fixture supplies metadata required by the hardened reentrant path check.

## Scope and evidence limits

Trigger/state DDL, row formats, policy digests, occurrence identity, CAS semantics, retention, scheduler decisions, and public APIs are unchanged. The ledgers remain synthetic and deny-only: no timer, notification, consent, trusted clock, tool dispatch, or external action is authorized. Repeated pathname checks are not atomic `dirfd` custody or protection against hostile concurrent filesystem renames.

No live data, credentials, hardware, paid/external compute, Candidate generation/promotion, protected V2 evaluation, frozen-contract change, main write/merge, or UI/frontend work occurred. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no scheduler production-readiness or ARK/JARVIS PASS is claimed.
