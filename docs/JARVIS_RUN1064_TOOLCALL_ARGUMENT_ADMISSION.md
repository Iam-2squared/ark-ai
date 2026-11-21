# Run1064 — frozen ToolCall argument admission

- Target: Draft PR #8, `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `87ee86a333fb851ef21b64ce91e9b15d15e231f6` (Run1062 foundation; exact-head CI run `44905799382` was GREEN).
- Child branch: `research/run1064-toolcall-argument-admission`.
- This child continues the existing isolated argument-admission source work; it does not change the frozen ToolCall v1 constructor or JSON contract.

## Change

- `ToolRegistry.bind()` now checks the original frozen argument carrier before reconstructing a ToolCall, so a reflected `MappingProxyType` backed by a foreign Mapping cannot run `__iter__`/`items` callbacks first.
- The bounded argument-admission constants must remain exact built-in integers; an equal-valued int subclass is rejected before resource-limit comparison.
- Direct PermissionGate and registry-authoritative authorization retain their pre-hash argument admission ordering.
- Five synthetic regressions cover registry binding, direct gate admission, registered gate admission, exact resource-limit types, and valid nested multilingual JSON binding.

## Evidence and limits

The tests use a disposable in-process registry/gate and a foreign Mapping that records or raises on access. No backend dispatch occurs. No local pytest/Ruff PASS or child CI verdict is claimed here; the new exact-head CI must certify the completed child.

This is a local Python-process input-integrity boundary, not a sandbox, authenticated consent, trusted clock, remote backend attestation, cross-store atomicity, or proof of an external effect. ToolCall v1 schema/API, Memory v1, Planner v1, Observation Envelope v1, ActionAudit v1 and all frozen V1/V2/Local UI/Launcher evidence remain unchanged. No UI, paid service, external compute, Candidate, protected V2 evaluation, credentials, physical hardware, or main merge is involved. PR #5 remains Draft/unmerged.
