# Run1155 — PermissionGate denial-order rebase

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `9b1dbc439ec338e2840d9dc493e724c651617e60`.
- Rebased from Draft PR #339 exact child HEAD: `7b07253ec587ef458aac5adad00b7c00c7d77a51`.
- Source exact-head CI: [45115302796](https://github.com/Iam-2squared/ark-ai/actions/runs/45115302796) GREEN, 6/6 on the source head only; it does not transfer to this rebase.
- New child branch: `research/run1155-planner-permission-rebase-latest`.
- Existing regression: `tests/test_registered_policy_spend_rebind_run379.py`.

## Finding and change

The predecessor exact-head run [45102298063](https://github.com/Iam-2squared/ark-ai/actions/runs/45102298063) exposed an over-specific assertion about diagnostic ordering. During a registered capability mutation, PermissionGate can correctly reject earlier with the ToolSpec/call mismatch rather than reaching the later registered-identity diagnostic.

The rebased regression asserts the security invariant instead: the mutated registration cannot succeed, the one-shot token remains unconsumed, restoring the original registration permits the token to be spent, and an unchanged registry still spends exactly once. It does not freeze which fail-closed diagnostic wins when multiple checks can reject the mutation.

No production PermissionGate, ToolRegistry, token, or policy semantics changed.

## Evidence boundary

Test-only correction. No real backend execution, durable authorization, trusted consent, paid compute, Candidate, protected V2 evaluation, UI/frontend work, frozen-contract change, or main merge is included. Fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required; no local test result is claimed. PR #8 and PR #5 remain Draft/unmerged; PR #9 remains untouched; ARK/JARVIS remains NOT_PASSED.
