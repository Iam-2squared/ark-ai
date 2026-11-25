# Run1433 — Proactive state absent-hook custody on latest foundation

## Exact basis

- Parent Draft PR #8 branch: `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `c6ee53c5e5671b926b7625da7a7b5dfdd41ae7d3`.
- Rebased from Draft PR #609, branch `research/rebase-run1417-proactive-state-absent-hook-custody-20261126`, exact prior child HEAD `7dbdefaaec8f58b9a681d9e902dd48aa372411cd`.
- Parent source blob before reapplication: `ef8503824a03dae48d04d46bb31e6ea0943e433c`; identical to the prior child's source base.
- Source: `src/ark/proactive_state_ledger.py`; regression module: `tests/test_proactive_state_absent_hook_custody_run1417.py`.

## Change

Retains true-absence sentinels and import-time class/policy epochs for the proactive state ledger's authority-bearing classes and hooks. The guards distinguish absent hooks from explicit `None`/sentinel replacement and validate retained aliases/epochs before inspecting or using the original class definitions.

## Regression coverage

The rebased synthetic tests cover absent-hook installation/substitution and the expected fail-closed behavior before state-ledger operations. All storage remains local and synthetic; no timer, notification, external action, or ToolBackend dispatch is invoked.

## Scope and evidence limits

Proactive state schema, row format, policy digests, occurrence identity, CAS semantics, retention, scheduler decisions, and public APIs are unchanged. This is in-process class/policy integrity only; it is not a sandbox, trusted clock, independent storage custody, authenticated consent, or exactly-once external-effect proof.

No live personal data, credentials, hardware, paid/external compute, Candidate generation/promotion, protected V2 evaluation, frozen-contract change, main write/merge, or UI/frontend work occurred. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no scheduler production-readiness or ARK/JARVIS PASS is claimed.
