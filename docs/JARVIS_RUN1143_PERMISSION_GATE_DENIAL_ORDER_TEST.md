# Run1143 — PermissionGate denial-order regression

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Work-basis HEAD: `e7b49bfb257b0adaf07b3e7b2e52e7f4ca2bf6e8`.
- Child branch: `research/run1143-permission-gate-denial-order-test`.
- Existing regression: `tests/test_registered_policy_spend_rebind_run379.py`.

## Finding

Exact-head CI run [45102298063](https://github.com/Iam-2squared/ark-ai/actions/runs/45102298063) exposed one assertion failure on Ubuntu / Python 3.12. The test changed a registered tool's `capability` while the authorization thread waited at the one-shot spend lock. The gate correctly denied the call earlier with `tool call does not match registered tool specification`, before the later registered-identity diagnostic could run. The token remained unconsumed; the failure was an over-specific test assertion about diagnostic ordering, not an authorization bypass.

## Change

The regression now asserts the security invariant: the mutated registration cannot succeed, the one-shot token remains unconsumed, and restoring the original registration allows the token to be spent. It deliberately does not require one particular `PermissionDenied` message when multiple fail-closed checks can reject the same mutation.

No production PermissionGate, ToolRegistry, token, or policy semantics changed.

## Evidence boundary

Test-only correction. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required. The failing run above is on the predecessor child head and is not evidence for this branch. No local test result is claimed. No real backend execution, durable authorization, trusted consent, paid compute, Candidate, protected V2 evaluation, UI/frontend work, frozen-contract change, or main merge is included. PR #8 and PR #5 remain Draft/unmerged; PR #9 remains untouched; ARK/JARVIS remains NOT_PASSED.
