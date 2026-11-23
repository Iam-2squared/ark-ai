# JARVIS Run1229 — PermissionGate slot deletion custody on latest foundation

## Exact basis

- Repository: `Iam-2squared/ark-ai`.
- Parent: Draft PR #8, branch `research/jarvis-foundations`.
- Exact parent work-basis HEAD: `0f4343ff36f23b1acb7ae1907b1be5ea98556c0d`.
- Reapplies the isolated deletion-custody finding from Draft PR #408 exact child HEAD `ac35b3cfcd6032d67516cf8dfe67142a36f28095`.
- Predecessor exact-head CI [45272526386](https://github.com/Iam-2squared/ark-ai/actions/runs/45272526386) was GREEN 6/6 on that child only; it does not transfer to this rebase.
- New child branch: `research/run1229-permission-gate-delete-seal-latest`.

## Finding and repair

The current PermissionGate seals ordinary assignment and checks token/lock slot epochs before authorization, but it did not define `__delattr__`. Python's default slot deletion therefore allowed ordinary deletion of `_consumed_tokens`, `_token_lock`, their epoch witnesses, or `_sealed`. Later authorization checks fail closed when state is missing, but the public object remained ordinarily mutable.

This rebase adds a sealed deletion guard and pins the exact `__delattr__` descriptor in the class-identity check. Regression tests attempt deletion of every state slot and verify that replacing the class deletion guard is rejected before authorization executes it.

## Evidence boundary

This is local in-process object-integrity hardening only. It does not create durable approval, trusted time, authenticated consent, external execution authority, or exactly-once external effects. ToolRegistry, frozen ToolCall/PermissionGate contracts, Planner schema, V1/V2/Local UI/Launcher evidence and V3 evaluation boundaries are unchanged. Synthetic tests only; fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required.

No paid/external compute, Candidate generation/promotion, protected V2 evaluation, credentials, hardware, UI/frontend work, destructive operation, frozen-contract change, or main merge. PR #5 and #8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
