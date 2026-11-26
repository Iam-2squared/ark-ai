# Run1068 — proactive schedule preview helper identity rebase

## Exact work basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent HEAD: `5d9e1dfb37d7ff0769545e790da9d5dfbfeb8c50` (Run1067 checkpoint; parent CI run `44912347493` GREEN, 6/6).
- Original isolated package: Draft PR #195, exact child HEAD `98d6c28fda04cb1ebae0f6c563699ce965aa113f`; its exact-head CI run `44912003073` was GREEN, 6/6 on the older parent `38644f86ce260ae1f264ac7564a8c974f1e83379`.
- Rebased child branch: `research/run1068-schedule-preview-helper-identity-rebase`.
- This rebase requires fresh exact-head CI; historical green evidence is not transferred.

## Gap and change

The disconnected recurrence preview pinned recurrence data constants and dataclass descriptors, but did not pin the internal `_valid_policy` and `_occurrence` helper identities. A rebound helper could bypass policy admission or supply a forged occurrence identifier while the surrounding checks remained unchanged.

- Capture the import-original policy validator and occurrence-identity helper.
- Reject either helper being rebound in the existing fail-closed protocol guard, before the substituted helper can run.
- Preserve recurrence formula, cursor format, result fields, and deny-only flags.

## Regression coverage

A synthetic test independently replaces each helper with a sentinel that records and raises if called. The preview must reject the substitution before invocation, then continue to produce the original deterministic `DUE_UNVERIFIED` fixture after restoration.

## Limits and safety

This is local Python module-integrity defense, not a sandbox or protection against arbitrary code execution in the same process. Schedule clocks and cursors remain caller asserted. No timer, notification, model call, tool dispatch, consent, trusted clock, or external effect is introduced. Quarantine ledger, durable scheduler state, and production scheduler integration are unchanged.

No paid service, external compute, credentials, physical-device action, Candidate generation/promotion, protected V2 evaluation, frozen-contract change, main merge, UI/frontend work, PR #5, or PR #9 is involved.

**ARK/JARVIS remains NOT_PASSED.**
