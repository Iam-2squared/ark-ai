# JARVIS Run1232 — PermissionGate slot deletion custody on current foundation

## Exact basis

- Repository: `Iam-2squared/ark-ai`.
- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `e3ab3b4a33ff2414bc978158898a2eed71ef79f5`.
- Reapplies the isolated deletion-custody package from Draft PR #413, exact child HEAD `e75d49e16cdb35039910e20ab5e988e780110fb3`.
- Predecessor exact-head CI [45283136915](https://github.com/Iam-2squared/ark-ai/actions/runs/45283136915) was GREEN 6/6 on its older base; it does not transfer to this rebase.
- New child branch: `research/run1232-permission-gate-delete-seal-rebase`.

## Finding and repair

The PermissionGate seals ordinary assignment and checks token/lock slot epochs before authorization, but it did not define `__delattr__`. Python's default slot deletion therefore allowed ordinary deletion of `_consumed_tokens`, `_token_lock`, their epoch witnesses, or `_sealed`. Later authorization checks fail closed when state is missing, but the public object remained ordinarily mutable.

This rebase adds a sealed deletion guard and pins the exact `__delattr__` descriptor in the class-identity check. Regression tests attempt deletion of every state slot and verify that replacing the class deletion guard is rejected before authorization executes it.

## Evidence boundary

This is local in-process object-integrity hardening only. It does not create durable approval, trusted time, authenticated consent, external execution authority, or exactly-once external effects. ToolRegistry, frozen ToolCall/PermissionGate contracts, Planner schema, V1/V2/Local UI/Launcher evidence and V3 evaluation boundaries are unchanged. Synthetic tests only; fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required.

No paid/external compute, Candidate generation/promotion, protected V2 evaluation, credentials, hardware, UI/frontend work, destructive operation, frozen-contract change, or main merge. PR #5 and #8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
