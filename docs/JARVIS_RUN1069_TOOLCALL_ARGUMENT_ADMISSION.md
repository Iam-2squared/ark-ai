# Run1069 — frozen ToolCall argument admission rebase

## Exact work basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent HEAD: `5d9e1dfb37d7ff0769545e790da9d5dfbfeb8c50` (Run1067 checkpoint; parent CI run `44912347493` GREEN, 6/6).
- Original source package: Draft PR #190, exact child HEAD `f79e5cd38aaeb338fdc50fcf61e22ff638c5f103`; exact-head CI run `44908939702` FAIL, 6/6 because six legacy assertions expected the later identity diagnostic.
- Diagnostic-only repair: Draft PR #194, exact child HEAD `15da8e19e761d3bb4335b179f77ccf440b0cc82f`; exact-head CI run `44911687790` GREEN, 6/6 on the older PR #190 branch.
- Rebased child branch: `research/run1069-toolcall-argument-admission-rebase`.
- This combined rebase requires fresh exact-head CI; neither historical result transfers.

## Change

- Preserve frozen ToolCall v1's general Mapping construction contract.
- Add bounded, exact-type admission for the recursively frozen JSON carrier at the opt-in ToolRegistry and PermissionGate boundary.
- Reject MappingProxyType whose actual backing object is not an exact built-in dict before foreign mapping callbacks can execute.
- Validate resource-limit constants as exact built-in integers before comparisons.
- Invoke admission before request hashing, grant iteration and registry/policy callbacks.
- Update three legacy diagnostic assertions to accept either the earlier argument-carrier rejection or the existing identity rejection. The operations must still fail closed before grant completion/backend dispatch.

## Regression coverage

Five new synthetic cases cover registry binding, direct PermissionGate, registry-authoritative PermissionGate, hostile equal-valued integer-subclass limits, and valid nested multilingual JSON. Existing registry/policy epoch tests retain their denial assertions with compatible diagnostic matching.

## Evidence and limits

No local pytest/Ruff PASS is claimed; fresh exact-head CI is required. No backend dispatch occurs. This is a local Python-process input-integrity boundary, not a sandbox, authenticated consent, trusted clock, remote backend attestation, cross-store atomicity, or proof of an external effect.

ToolCall v1 schema/API, Memory v1, Planner v1, Observation Envelope v1, ActionAudit v1 and frozen V1/V2/Local UI/Launcher evidence remain unchanged. No UI, paid service, external compute, Candidate, protected V2 evaluation, credentials, physical hardware, real ToolBackend, or main merge is involved. PR #5 remains Draft/unmerged.

**ARK/JARVIS remains NOT_PASSED.**
