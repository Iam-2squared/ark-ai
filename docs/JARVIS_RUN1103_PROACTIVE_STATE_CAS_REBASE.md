# Run1103 — proactive eligibility CAS rebase and row-time fix

## Exact basis

- Repository: `Iam-2squared/ark-ai`
- Superseded stale child: Draft PR #227, `research/run1091-proactive-state-cas`
- Original child HEAD: `3952c0ee9a8242e137679347da7d998e5ca6b303`
- Original CI: [run 44982299323](https://github.com/Iam-2squared/ark-ai/actions/runs/44982299323), **FAIL across all six matrix jobs**.
- Current parent: Draft PR #8, `research/jarvis-foundations`, exact HEAD `e8761e183094cd27955423844a8db7d6b0063829`
- Rebased child: `research/run1103-proactive-state-cas-rebase-fix`
- Source: `src/ark/proactive_state_ledger.py`
- Tests: `tests/test_proactive_state_ledger_run1091.py` (11 test functions)

## Failure and correction

The old exact-head CI ran 19,224 passing tests and one skip, but all six OS/Python jobs failed in the same 9 proactive-state tests. The row validator's temporal invariant was inverted:

- Required invariant: `last_proposal_at_ms <= last_evaluated_at_ms`.
- Previous rejection predicate: `proposal_at <= evaluated_at`, which rejected every valid row.
- Correction: reject only when `proposal_at > evaluated_at`.

The schema, row digest format, CAS algorithm, timestamp semantics, and non-authority behavior are unchanged. The existing 11-test suite is rebased unchanged so the corrected source is checked against its original restart, cooldown, exact-boundary, CAS-race, corruption and denial expectations.

## Limits

This is content-minimized local eligibility state only. Caller timestamps remain unauthenticated; checksums are not authenticated provenance; `ELIGIBLE_PREVIEW` is not consent, notification permission, trusted time, dispatch or replay authority. No live scheduler, timer, notification, observation source, model, ToolBackend, paid/external compute, Candidate, protected V2 evaluation, frozen contract, UI/frontend, credentials, physical hardware or main merge is involved. The original PR #227 remains open/Draft and unmodified.

Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required on this rebased branch. No local pytest/Ruff PASS is claimed. **ARK/JARVIS remains NOT_PASSED.**
