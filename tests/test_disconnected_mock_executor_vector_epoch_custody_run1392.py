"""Run1392: mock executor retains its complete validator vector epoch."""

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
)
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore


def test_joint_validator_vector_replacement_is_denied_before_mock_and_audit(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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
    gate = PermissionGate()
    audit = SQLiteActionAudit(
        tmp_path / "action-audit.sqlite3",
        clock_ms=lambda: 100,
    )
    occurrences = SyntheticOccurrenceStore(tmp_path / "occurrences.sqlite3")
    executor = DisconnectedMockExecutor(registry, gate, audit, occurrences)
    call = ToolCall(
        "fixture.mock",
        "fixture.mock",
        "synthetic:private",
        {"value": "fixture-only"},
    )
    grant = CapabilityGrant("fixture.mock", "synthetic:private")
    empty: tuple[object, ...] = ()
    vector_names = (
        "_MOCK_BACKEND_METHODS", "_ORIGINAL_MOCK_BACKEND_METHODS",
        "_MOCK_RESULT_FIELDS", "_ORIGINAL_MOCK_RESULT_MEMBERS",
        "_MOCK_RESULT_HOOKS", "_ORIGINAL_MOCK_RESULT_HOOKS",
        "_RECEIPT_FIELDS", "_RECEIPT_DENIALS", "_RECEIPT_HOOKS",
        "_ORIGINAL_RECEIPT_MEMBERS", "_ORIGINAL_RECEIPT_HOOKS",
    )
    for name in vector_names:
        monkeypatch.setattr(executor_module, name, empty)
    monkeypatch.setattr(
        executor_module,
        "_ORIGINAL_COMPONENT_VECTOR_EPOCH",
        tuple(empty for _ in vector_names),
    )
    descriptor_calls: list[str] = []

    monkeypatch.setattr(
        MockExecutionReceipt,
        "dispatch_authorized",
        property(
            lambda _instance: (
                descriptor_calls.append("dispatch_authorized"),
                True,
            )[1],
        ),
    )

    with pytest.raises(
        DisconnectedMockExecutionRejected,
        match="validator inventory changed",
    ):
        executor.execute(call, (grant,), now_ms=10)

    assert descriptor_calls == []
    assert backend.calls == 0
    assert audit.events() == []
