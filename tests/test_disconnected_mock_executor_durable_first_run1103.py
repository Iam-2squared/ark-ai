"""Durable-first WRITE ordering for the disconnected mock executor."""

from __future__ import annotations

import pytest

from ark.agency import (
    CapabilityGrant,
    Effect,
    OneShotAuthorization,
    PermissionGate,
    SQLiteActionAudit,
    ToolCall,
    ToolRegistration,
    ToolRegistry,
)
from ark.agency.disconnected_mock_executor import (
    DisconnectedMockExecutionRejected,
    DisconnectedMockExecutor,
    MockToolBackend,
)
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore


def _write_stack(tmp_path, *, token_id: str = "run1103-token"):
    backend = MockToolBackend()
    registry = ToolRegistry((
        ToolRegistration(
            "fixture.mock",
            "fixture.mock",
            Effect.WRITE,
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
    token = OneShotAuthorization(token_id, call.request_id, 500)
    return backend, registry, gate, audit, occurrences, executor, call, grant, token


def test_duplicate_durable_reservation_does_not_spend_executor_gate(tmp_path):
    (
        backend, registry, gate, audit, occurrences, executor,
        call, grant, token,
    ) = _write_stack(tmp_path)
    occurrences.reserve_synthetic(
        registry,
        call,
        token,
        occurrence_id="occ_" + "a" * 64,
        now_ms=100,
    )

    with pytest.raises(
        DisconnectedMockExecutionRejected,
        match="durable synthetic occurrence reservation failed",
    ):
        executor.execute(
            call,
            (grant,),
            now_ms=100,
            one_shot=token,
            occurrence_id="occ_" + "b" * 64,
        )

    assert gate._consumed_tokens == set()
    assert occurrences.count_synthetic() == 1
    assert backend.calls == 0
    assert audit.events() == []


def test_actual_gate_denial_after_reservation_leaves_token_durably_burned(tmp_path):
    (
        backend, registry, gate, audit, occurrences, executor,
        call, grant, token,
    ) = _write_stack(tmp_path, token_id="run1103-preconsumed-token")
    gate.authorize_registered(
        registry,
        call,
        (grant,),
        now_ms=100,
        one_shot=token,
    )
    assert token.token_id in gate._consumed_tokens

    with pytest.raises(
        DisconnectedMockExecutionRejected,
        match="local PermissionGate denied after durable reservation",
    ):
        executor.execute(
            call,
            (grant,),
            now_ms=100,
            one_shot=token,
            occurrence_id="occ_" + "c" * 64,
        )

    assert occurrences.count_synthetic() == 1
    assert backend.calls == 0
    assert audit.events() == []


def test_missing_exact_scope_grant_fails_before_durable_reservation(tmp_path):
    (
        backend, _registry, gate, audit, occurrences, executor,
        call, _grant, token,
    ) = _write_stack(tmp_path, token_id="run1103-denied-token")
    wrong_grant = CapabilityGrant("other.capability", "synthetic:private")

    with pytest.raises(
        DisconnectedMockExecutionRejected,
        match="local PermissionGate denied the mock operation",
    ):
        executor.execute(
            call,
            (wrong_grant,),
            now_ms=100,
            one_shot=token,
            occurrence_id="occ_" + "d" * 64,
        )

    assert gate._consumed_tokens == set()
    assert occurrences.count_synthetic() == 0
    assert backend.calls == 0
    assert audit.events() == []


def test_write_grant_generator_failure_fails_before_reservation(tmp_path):
    (
        backend, _registry, gate, audit, occurrences, executor,
        call, grant, token,
    ) = _write_stack(tmp_path, token_id="run1103-generator-token")

    def grants():
        yield grant
        raise RuntimeError("synthetic grant source failure")

    with pytest.raises(
        DisconnectedMockExecutionRejected,
        match="local PermissionGate denied the mock operation",
    ):
        executor.execute(
            call,
            grants(),
            now_ms=100,
            one_shot=token,
            occurrence_id="occ_" + "e" * 64,
        )

    assert gate._consumed_tokens == set()
    assert occurrences.count_synthetic() == 0
    assert backend.calls == 0
    assert audit.events() == []


def test_success_consumes_actual_gate_only_after_durable_reservation(tmp_path):
    (
        backend, _registry, gate, audit, occurrences, executor,
        call, grant, token,
    ) = _write_stack(tmp_path, token_id="run1103-success-token")

    receipt = executor.execute(
        call,
        (grant,),
        now_ms=100,
        one_shot=token,
        occurrence_id="occ_" + "f" * 64,
    )

    assert token.token_id in gate._consumed_tokens
    assert occurrences.count_synthetic() == 1
    assert backend.calls == 1
    assert receipt.mock_only is True
    assert receipt.dispatch_authorized is False
    assert receipt.external_effect_proven is False
    assert [event.outcome for event in audit.events()] == [
        "mock_pre_action",
        "mock_completed",
    ]
