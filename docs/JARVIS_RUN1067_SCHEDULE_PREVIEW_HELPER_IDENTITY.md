# Run1067 — proactive schedule preview helper identity

## Exact work basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent HEAD: `38644f86ce260ae1f264ac7564a8c974f1e83379` (Run1063 mock-only executor integrated; parent CI run `44911305869` was in progress when this child was prepared).
- Child branch: `research/run1067-schedule-preview-helper-identity`.
- Scope: `src/ark/disconnected_schedule_preview.py` and one synthetic regression test.
- No frozen Observation, ToolCall, Memory, Planner, or V3 contract is changed.

## Gap

The preview's denial guard pinned the recurrence data constants and dataclass descriptors, but it did not pin the internal `_valid_policy` and `_occurrence` helper function identities. A rebound helper could therefore bypass policy admission or supply a forged occurrence identifier while the surrounding data/constructor checks remained unchanged.

## Change

- Capture the import-original policy validator and occurrence-identity helper.
- Reject either helper being rebound in the existing fail-closed protocol guard, before the substituted helper can run.
- Preserve the recurrence formula, cursor format, result fields, and all deny-only flags.

## Regression coverage

A synthetic test independently replaces each helper with a sentinel that records and raises if called. The preview must reject the substituted helper before invocation, then continue to produce the original deterministic `DUE_UNVERIFIED` fixture after the monkeypatch is restored.

## Limits and safety

This is a local Python module-integrity check, not a sandbox or protection against arbitrary code execution in the same process. Schedule clocks and cursors remain caller asserted; no timer, notification, model call, tool dispatch, consent, trusted clock, or external effect is introduced. The quarantine ledger, durable scheduler state, and production scheduler integration are unchanged.

No paid service, external compute, credential, physical-device action, Candidate generation/promotion, protected V2 evaluation, main merge, UI/frontend work, PR #5, or PR #9 is involved. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no local test PASS is claimed.

**ARK/JARVIS remains NOT_PASSED.**
