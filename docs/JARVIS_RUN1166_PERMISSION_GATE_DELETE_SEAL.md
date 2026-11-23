# Run1166 — PermissionGate slot deletion custody

## Exact basis

- Parent: Draft PR #8, `research/jarvis-foundations`.
- Exact parent HEAD at branch creation: `c12bd530bceacaea47122a9a9010d3a3b5fd6245`.
- New branch: `research/run1166-permission-gate-delete-seal`.
- Production source: `src/ark/agency/policy.py`; regression: `tests/test_permission_gate_delete_seal_run1166.py`.

## Finding and repair

The exact-type PermissionGate already sealed ordinary assignment and verified its token/lock slot epochs before authorization, but it did not define `__delattr__`. Python's default slot deletion therefore allowed ordinary deletion of `_consumed_tokens`, `_token_lock`, their epoch witnesses, or `_sealed`; later checks would fail closed, but the public object could still be mutated through a normal attribute operation.

This package adds a sealed deletion guard that rejects deletion after construction and pins the exact `__delattr__` descriptor in the class-identity check. Tests attempt deletion of every state slot and verify that replacing the class deletion guard is rejected before authorization enters it.

## Evidence boundary

This is a local in-process object-integrity hardening change. It does not create durable approval, trusted time, authenticated consent, external execution authority, or exactly-once external effects. No ToolRegistry, frozen ToolCall/PermissionGate contract, planner schema, V1/V2/Local UI/Launcher evidence, or V3 evaluation boundary is changed. Synthetic unit tests only; fresh exact-head Windows/Linux × Python 3.11–3.13 CI is required.

No paid/external compute, Candidate generation/promotion, protected V2 evaluation, credentials, hardware, UI/frontend work, destructive operation, or main merge. PR #5 and #8 remain Draft/unmerged; PR #9 remains untouched. ARK/JARVIS remains NOT_PASSED.
