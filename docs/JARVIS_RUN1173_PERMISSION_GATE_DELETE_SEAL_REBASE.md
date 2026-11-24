# Run1173 — PermissionGate slot deletion custody rebase

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent HEAD at branch creation: `107b56849fec47e4d2e24576958b358c0aef697b`.
- Rebased the production source and regression from Draft PR #355 exact child HEAD `004ea823d275def58d55ec4f9af8890c55a0c32b`.
- Source exact-head CI [45141976504](https://github.com/Iam-2squared/ark-ai/actions/runs/45141976504) was GREEN on the prior child head only; it does not transfer to this rebase.
- New branch: `research/run1173-permission-gate-delete-seal-rebase`.

## Finding and repair

The exact-type PermissionGate already sealed ordinary assignment and verified its token/lock slot epochs before authorization, but it did not define `__delattr__`. Python's default slot deletion therefore allowed ordinary deletion of `_consumed_tokens`, `_token_lock`, their epoch witnesses, or `_sealed`; later checks would fail closed, but the public object could still be mutated through a normal attribute operation.

This package adds a sealed deletion guard that rejects deletion after construction and pins the exact `__delattr__` descriptor in the class-identity check. Tests attempt deletion of every state slot and verify that replacing the class deletion guard is rejected before authorization enters it.

## Evidence boundary

This is local in-process object-integrity hardening only. It does not create durable approval, trusted time, authenticated consent, external execution authority, or exactly-once external effects. No ToolRegistry, frozen ToolCall/PermissionGate contract, planner schema, V1/V2/Local UI/Launcher evidence, or V3 evaluation boundary is changed. Synthetic unit tests only; fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required.

No paid/external compute, Candidate generation/promotion, protected V2 evaluation, credentials, hardware, UI/frontend work, destructive operation, or main merge. PR #5 and #8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
