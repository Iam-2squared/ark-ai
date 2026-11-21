# ARK AI Run1030 — Action Audit outcome byte and control boundary

**Work basis:** Draft PR #8 branch `research/jarvis-foundations`, exact HEAD `b585c61a6e3ca1a9f456175b2a96053a908a500c`. Re-applies the isolated PR #13 hardening onto the current foundation source without changing the frozen Action Audit v1 schema or public event fields.

## Change

- Keep the existing open outcome vocabulary, but require exact built-in text bounded to 256 code points and 256 UTF-8 bytes.
- Reject C0/C1, bidi, Unicode formatting and line-separator controls before SQLite open or clock sampling.
- Apply the same validation to persisted rows; oversized TEXT is rejected in SQLite-side byte preflight before Python hydration.
- Preserve caller `ValueError` behavior and fail closed with `ActionAuditSchemaError` for corrupt persisted history.

## Historical evidence (not transferred)

Previous PR #13 head `b940525c43d3e3a858352c8702dc4202598597e3` passed exact-head CI run #44518002802 (6/6). That result applies only to its previous source base. Fresh exact-head CI is required; no local pytest/Ruff PASS is claimed.

## Limits

Synthetic ToolCall values and disposable SQLite only. This is local input/resource integrity, not an authenticated event chain, independent custody, trusted time, consent, cross-store atomicity, or proof of an external effect. No ToolBackend, paid service, external compute, Candidate, protected V2 evaluation, UI, PR #5, PR #9 or main merge.
