# ARK AI Run1017 — Action Audit outcome budget custody

**Work basis:** PR #60 exact head `33a38f60e8503b52bd77b6016777f7d5ffebd676`, branch `research/action-audit-outcome-bounds-run1016`. Parent exact-head CI run [#44698108036](https://github.com/Iam-2squared/ark-ai/actions/runs/44698108036) completed GREEN 6/6. This is an isolated non-UI child of PR #60; it does not modify PR #8, main, frozen contracts, or UI branches.

## Finding

The Run1016 outcome validator compared the mutable module globals `_MAX_AUDIT_OUTCOME_CHARS` and `_MAX_AUDIT_OUTCOME_BYTES` with the mutable `_ORIGINAL_AUDIT_OUTCOME_BUDGETS` tuple. Coordinated rebinding of all three could preserve the validator function identity while increasing the accepted limits. The existing `_require_original_event_constructor` guard checked the validator function identity but did not independently pin the two numeric limits.

## Change

The process-integrity guard now requires both budget globals to remain exact integers with the original value 256 before audit input validation, SQLite connection, or clock sampling. The v1 schema, event shape, open outcome vocabulary, and 256-code-point / 256-byte policy are unchanged.

## Regression

One synthetic test coordinates rebinding of both limits and the comparison tuple, then requires `ActionAuditSchemaError` before the SQLite connection hook or clock can run. It uses a disposable temporary database path only; no existing user database is opened.

## Evidence and limits

The test is authored, not a local pytest PASS. New exact-head Windows/Linux × Python 3.11–3.13 CI is required. This remains local process-integrity hardening, not a Python sandbox, authenticated audit provenance, trusted time, consent, cross-store atomicity, or external-effect proof.

No real ToolBackend, live personal data, paid service, external compute, credentials, Candidate, protected V2 evaluation, frozen-contract change, UI work, PR #5, PR #9, or main merge is included. PR #8 remains Draft/unmerged. ARK/JARVIS remains NOT_PASSED.
