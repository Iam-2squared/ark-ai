import sqlite3

import pytest

from ark.agency import (
    ActionAuditSchemaError,
    CapabilityGrant,
    Effect,
    OneShotAuthorization,
    PermissionDenied,
    PermissionGate,
    PlanConflictError,
    PlanGraph,
    PlanStep,
    SQLiteActionAudit,
    StepState,
    ToolCall,
    ToolSpec,
)


def test_tool_call_identity_is_canonical() -> None:
    left = ToolCall("files.read", "files.read", "workspace:a", {"b": 2, "a": 1})
    right = ToolCall("files.read", "files.read", "workspace:a", {"a": 1, "b": 2})
    assert left.arguments_sha256 == right.arguments_sha256
    assert left.request_id == right.request_id


def test_permission_gate_requires_exact_capability_and_scope() -> None:
    gate = PermissionGate()
    spec = ToolSpec("files.read", "files.read", Effect.READ)
    call = ToolCall("files.read", "files.read", "workspace:a")
    with pytest.raises(PermissionDenied):
        gate.authorize(spec, call, [], now_ms=10)
    with pytest.raises(PermissionDenied):
        gate.authorize(
            spec,
            call,
            [CapabilityGrant("files.read", "workspace:b")],
            now_ms=10,
        )
    gate.authorize(spec, call, [CapabilityGrant("files.read", "workspace:a")], now_ms=10)


def test_expired_grant_fails_closed() -> None:
    gate = PermissionGate()
    spec = ToolSpec("files.read", "files.read")
    call = ToolCall("files.read", "files.read", "workspace:a")
    with pytest.raises(PermissionDenied, match="no active"):
        gate.authorize(
            spec,
            call,
            [CapabilityGrant("files.read", "workspace:a", expires_at_ms=10)],
            now_ms=10,
        )


def test_write_effect_requires_exact_consumable_one_shot() -> None:
    gate = PermissionGate()
    spec = ToolSpec("files.write", "files.write", Effect.WRITE)
    call = ToolCall("files.write", "files.write", "workspace:a", {"path": "x"})
    grant = CapabilityGrant("files.write", "workspace:a")
    with pytest.raises(PermissionDenied, match="one-shot"):
        gate.authorize(spec, call, [grant], now_ms=10)

    wrong = OneShotAuthorization("t1", "act_" + "0" * 64, 100)
    with pytest.raises(PermissionDenied, match="does not match"):
        gate.authorize(spec, call, [grant], now_ms=10, one_shot=wrong)

    token = OneShotAuthorization("t2", call.request_id, 100)
    gate.authorize(spec, call, [grant], now_ms=10, one_shot=token)
    with pytest.raises(PermissionDenied, match="already consumed"):
        gate.authorize(spec, call, [grant], now_ms=10, one_shot=token)


def _plan() -> PlanGraph:
    read = PlanStep("read", ToolCall("files.read", "files.read", "workspace:a"))
    write = PlanStep(
        "write",
        ToolCall("files.write", "files.write", "workspace:a"),
        depends_on=("read",),
    )
    verify = PlanStep(
        "verify",
        ToolCall("files.read", "files.read", "workspace:a"),
        depends_on=("write",),
    )
    return PlanGraph((read, write, verify))


def test_plan_rejects_unknown_dependency_and_cycles() -> None:
    call = ToolCall("noop", "noop", "scope")
    with pytest.raises(ValueError, match="unknown dependency"):
        PlanGraph((PlanStep("a", call, ("missing",)),))
    with pytest.raises(ValueError, match="cycle"):
        PlanGraph((PlanStep("a", call, ("b",)), PlanStep("b", call, ("a",))))


def test_plan_ready_steps_and_revision_guarded_transitions() -> None:
    plan = _plan()
    assert [step.step_id for step in plan.ready_steps()] == ["read"]
    running = plan.transition("read", StepState.RUNNING, expected_revision=0)
    with pytest.raises(PlanConflictError, match="revision mismatch"):
        plan.transition("read", StepState.SUCCEEDED, expected_revision=0)
    plan.transition("read", StepState.SUCCEEDED, expected_revision=running.revision)
    assert [step.step_id for step in plan.ready_steps()] == ["write"]


def test_plan_cannot_run_step_before_dependencies() -> None:
    plan = _plan()
    with pytest.raises(PlanConflictError, match="dependencies"):
        plan.transition("write", StepState.RUNNING, expected_revision=0)


def test_failed_step_blocks_transitive_descendants() -> None:
    plan = _plan()
    running = plan.transition("read", StepState.RUNNING, expected_revision=0)
    plan.transition("read", StepState.FAILED, expected_revision=running.revision)
    statuses = plan.statuses()
    assert statuses["write"].state is StepState.BLOCKED
    assert statuses["verify"].state is StepState.BLOCKED


def test_action_audit_stores_hash_not_raw_arguments(tmp_path) -> None:
    audit = SQLiteActionAudit(tmp_path / "audit.sqlite3", clock_ms=lambda: 1000)
    call = ToolCall(
        "files.read",
        "files.read",
        "workspace:a",
        {"path": "private-name.txt"},
    )
    event = audit.append(call, outcome="allowed")
    assert event.arguments_sha256 == call.arguments_sha256
    assert "private-name.txt" not in repr(event)
    assert audit.events() == [event]

    with sqlite3.connect(tmp_path / "audit.sqlite3") as conn:
        rows = conn.execute("SELECT * FROM action_events").fetchall()
    assert "private-name.txt" not in repr(rows)


def test_action_audit_future_schema_fails_closed(tmp_path) -> None:
    path = tmp_path / "audit.sqlite3"
    with sqlite3.connect(path) as conn:
        conn.execute("PRAGMA user_version=999")
    with pytest.raises(ActionAuditSchemaError):
        SQLiteActionAudit(path)
