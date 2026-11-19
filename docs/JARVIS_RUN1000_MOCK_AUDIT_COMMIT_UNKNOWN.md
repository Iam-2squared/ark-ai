# Run1000 — Pre-action audit COMMIT-UNKNOWN blocks mock execution

**Work basis:** Draft PR #22 exact head `8dd522befb15e39b805a417744dd2fc89db49331`. This is a separate test-only child branch; PR #22 remains Draft/unmerged.

## Regression

The synthetic WRITE fixture first durably reserves its one-shot occurrence. The Action Audit then inserts and commits the `mock_pre_action` row, but the connection wrapper raises an injected SQLite error only after the native context manager has committed and before the caller receives the acknowledgement.

The executor must fail closed: the mock backend call count remains zero. A newly constructed PermissionGate, ActionAudit and occurrence store then attempt the same token/occurrence. The durable reservation rejects the retry before another audit append or backend call. The committed pre-action audit row remains visible after reopening.

This exercises the audit-before-action boundary at the lost-response edge, not merely a pre-COMMIT validation failure.

## Limits and boundaries

Only disposable SQLite files, a synthetic ToolCall, and the exact in-process `MockToolBackend` are used. The test does not claim cross-store atomicity, authenticated authorization, trusted time, external-effect delivery, or exactly-once real-world execution. A local occurrence reservation and audit row are not independently authenticated evidence.

No production source, frozen schema/contract, V1/V2 evaluation, V3 gate, UI branch, real ToolBackend, network, shell, device, model, notification, paid service, GPU, Candidate artifact, or main branch is changed.

**Validation:** authored test and report only. Exact-head CI is pending after the Draft PR is opened; no PASS is claimed. Overall ARK/JARVIS remains NOT_PASSED.
