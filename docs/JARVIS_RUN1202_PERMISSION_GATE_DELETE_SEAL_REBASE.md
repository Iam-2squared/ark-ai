# Run1202 — PermissionGate slot deletion custody rebase

## Exact basis

- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `f44bfea6ed45275252f5b115d4d0aa738da9faad`.
- Reapplies the isolated finding from Draft PR #357 (Run1173), exact child HEAD `48d069fe089285f704867f9e67dfb41480541824`; its CI run [45150662044](https://github.com/Iam-2squared/ark-ai/actions/runs/45150662044) was GREEN only on that earlier child head.
- New branch: `research/run1202-permission-gate-delete-seal-rebase`.

## Finding and repair

The exact-type PermissionGate seals ordinary assignment and checks its token/lock slot epochs before authorization, but the parent implementation did not define `__delattr__`. Python's default slot deletion therefore allowed ordinary deletion of `_consumed_tokens`, `_token_lock`, their epoch witnesses, or `_sealed`. Later authorization checks fail closed when state is missing, but the public object remained ordinarily mutable.

This rebase adds a sealed deletion guard and pins the exact `__delattr__` descriptor in the class-identity check. Regression tests attempt deletion of every state slot and verify that replacing the class deletion guard is rejected before authorization executes it.

## Evidence boundary

This is local in-process object-integrity hardening only. It does not create durable approval, trusted time, authenticated consent, external execution authority, or exactly-once external effects. ToolRegistry, frozen ToolCall/PermissionGate contracts, Planner schema, V1/V2/Local UI/Launcher evidence, and V3 evaluation boundaries are unchanged. Synthetic tests only; fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required.

No paid/external compute, Candidate generation/promotion, protected V2 evaluation, credentials, hardware, UI/frontend work, destructive operation, frozen-contract change, or main merge. PR #5 and #8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
