"""Run1409: disconnected mock executor rejects absent-hook substitutions."""

from __future__ import annotations

import pytest

import ark.agency.disconnected_mock_executor as executor_module
from ark.agency import (
    CapabilityGrant,
    Effect,
    PermissionGate,
    SQLiteActionAudit,
    ToolCall,
    ToolRegistration,
    ToolRegistry,
)
from ark.agency.disconnected_mock_executor import (
    DisconnectedMockExecutionRejected,
    DisconnectedMockExecutor,
    MockExecutionReceipt,
    MockToolBackend,
    MockToolResult,
)
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore


def _stack(tmp_path):
    backend = MockToolBackend()
    registry = ToolRegistry((
        ToolRegistration(
            "fixture.mock",
            "fixture.mock",
            Effect.READ,
            "ark.mock.fixture.v1",
            backend,
        ),
    ))
    audit = SQLiteActionAudit(
        tmp_path / "action-audit.sqlite3",
        clock_ms=lambda: 100,
    )
    occurrences = SyntheticOccurrenceStore(tmp_path / "occurrences.sqlite3")
    executor = DisconnectedMockExecutor(
        registry, PermissionGate(), audit, occurrences,
    )
    call = ToolCall(
        "fixture.mock",
        "fixture.mock",
        "synthetic:private",
        {"value": "fixture-only"},
    )
    grant = CapabilityGrant("fixture.mock", "synthetic:private")
    return backend, audit, executor, call, grant


@pytest.mark.parametrize(
    ("component", "hook"),
    [
        ("backend", "__new__"),
        ("backend", "__getattribute__"),
        ("backend", "__getattr__"),
        ("result", "__new__"),
        ("result", "__getattribute__"),
        ("result", "__getattr__"),
        ("receipt", "__new__"),
        ("receipt", "__getattribute__"),
        ("receipt", "__getattr__"),
    ],
)
@pytest.mark.parametrize("replacement_kind", ["explicit-none", "sentinel-installed"])
def test_absent_component_hooks_require_true_namespace_absence(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
    component: str,
    hook: str,
    replacement_kind: str,
) -> None:
    backend, audit, executor, call, grant = _stack(tmp_path)
    component_types = {
        "backend": MockToolBackend,
        "result": MockToolResult,
        "receipt": MockExecutionReceipt,
    }
    replacement = (
        None
        if replacement_kind == "explicit-none"
        else executor_module._ABSENT_CLASS_HOOK
    )
    monkeypatch.setattr(component_types[component], hook, replacement, raising=False)

    with pytest.raises(
        DisconnectedMockExecutionRejected,
        match="mock backend, result or receipt definition changed",
    ):
        executor.execute(call, (grant,), now_ms=10)

    assert object.__getattribute__(backend, "_calls") == 0
    assert audit.events() == []


def test_absence_sentinel_rebinding_is_denied_before_mock_or_audit(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    backend, audit, executor, call, grant = _stack(tmp_path)
    monkeypatch.setattr(executor_module, "_ABSENT_CLASS_HOOK", object())

    with pytest.raises(
        DisconnectedMockExecutionRejected,
        match="validator inventory changed",
    ):
        executor.execute(call, (grant,), now_ms=10)

    assert object.__getattribute__(backend, "_calls") == 0
    assert audit.events() == []
