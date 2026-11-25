# Run1373 — ToolRegistry admission guard self-custody

## Exact basis

- Parent: Draft PR #542, branch `research/run1363-tool-registry-delete-seal-rebase-20261125`.
- Exact parent HEAD: `7d0604a7a789f38f11d90faaf4c38516b5b55716`.
- Child branch: `research/run1373-registry-policy-guard-self-custody-20261125`.
- Source: `src/ark/agency/registry.py`.
- Regression: `tests/test_registry_policy_guard_self_custody_run1373.py`.

## Finding and correction

The registry's admission-limit, Unicode-policy and digest guards validated their dependencies but were still invoked through mutable module bindings. A substituted no-op could bypass exact identifier bounds/Unicode checks or the registry digest dependency check. The digest guard also called the two lower-level guards through their mutable bindings.

The source now retains import-original aliases for all three guards, verifies each mutable public binding against its retained function, and routes internal calls through the aliases. The digest guard also calls the retained limit and Unicode guards.

## Regression coverage

Synthetic tests replace each public guard with a no-op and require the retained original to reject before text/revision work. Additional tests replace the lower-level limit or Unicode guard and require the retained digest guard to reject before canonical serialization.

ToolRegistry registration semantics, revision format, registry mapping, ToolCall contract, PermissionGate behavior, backend binding and dispatch policy are unchanged.

## Scope and evidence limits

These are local in-process implementation-identity checks, not a security sandbox, remote backend attestation, trusted authorization, or permission to dispatch. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. No local pytest/Ruff PASS is claimed. No real backend, device/network I/O, paid/external compute, Candidate, protected V2 evaluation, credentials, hardware, destructive action, frozen-contract change, main merge, or UI/frontend work occurred. PR #5/#8/#9 and parent PR #542 remain Draft/unmerged; ARK/JARVIS remains NOT_PASSED.
