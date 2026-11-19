"""Disconnected mock executor integration; no real ToolBackend is dispatched."""

from __future__ import annotations

import sqlite3

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


def _stack(tmp_path, effect: Effect):
    backend = MockToolBackend()
    registry = ToolRegistry((
        ToolRegistration(
            "fixture.mock",
            "fixture.mock",
            effect,
            "ark.mock.fixture.v1",
            backend,
        ),
    ))
    gate = PermissionGate()
    ticks = []

    def clock_ms():
        ticks.append(100 + len(ticks))
        return ticks[-1]

    audit_path = tmp_path / "action-audit.sqlite3"
    occurrence_path = tmp_path / "occurrences.sqlite3"
    audit = SQLiteActionAudit(audit_path, clock_ms=clock_ms)
    occurrences = SyntheticOccurrenceStore(occurrence_path)
    executor = DisconnectedMockExecutor(registry, gate, audit, occurrences)
    call = ToolCall(
        "fixture.mock",
        "fixture.mock",
        "synthetic:private",
        {"value": "fixture-only"},
    )
    grant = CapabilityGrant("fixture.mock", "synthetic:private")
    return (
        backend, registry, gate, audit, occurrences, executor,
        call, grant, audit_path, occurrence_path,
    )


def test_read_requires_grant_and_commits_pre_and_completion_audit(tmp_path):
    backend, _, _, audit, _, executor, call, grant, _, _ = _stack(
        tmp_path, Effect.READ,
    )

    receipt = executor.execute(call, (grant,), now_ms=10)

    assert backend.calls == 1
    assert receipt.mock_only is True
    assert receipt.dispatch_authorized is False
    assert receipt.external_effect_proven is False
    assert receipt.automatic_replay_authorized is False
    assert receipt.occurrence_id is None
    events = audit.events()
    assert [event.outcome for event in events] == [
        "mock_pre_action", "mock_completed",
    ]
    assert receipt.pre_action_event_id == events[0].event_id
    assert receipt.completion_event_id == events[1].event_id


def test_write_reserves_durable_occurrence_before_mock_and_audits(tmp_path):
    backend, _, _, audit, occurrences, executor, call, grant, _, _ = _stack(
        tmp_path, Effect.WRITE,
    )
    token = OneShotAuthorization("synthetic-token-1", call.request_id, 500)
    occurrence_id = "occ_" + "a" * 64

    receipt = executor.execute(
        call,
        (grant,),
        now_ms=100,
        one_shot=token,
        occurrence_id=occurrence_id,
    )

    assert backend.calls == 1
    assert occurrences.count_synthetic() == 1
    assert receipt.occurrence_id == occurrence_id
    assert receipt.effect is Effect.WRITE
    assert receipt.exact_once_external_effect_proven is False
    assert [event.outcome for event in audit.events()] == [
        "mock_pre_action", "mock_completed",
    ]


def test_restarted_gate_cannot_reuse_durably_reserved_write_token(tmp_path):
    (
        backend, registry, _, audit, occurrences, executor,
        call, grant, _, occurrence_path,
    ) = _stack(tmp_path, Effect.WRITE)
    token = OneShotAuthorization("synthetic-token-restart", call.request_id, 500)
    first = "occ_" + "b" * 64
    second = "occ_" + "c" * 64

    executor.execute(
        call, (grant,), now_ms=100, one_shot=token, occurrence_id=first,
    )
    restarted_occurrences = SyntheticOccurrenceStore(occurrence_path)
    restarted = DisconnectedMockExecutor(
        registry, PermissionGate(), audit, restarted_occurrences,
    )

    with pytest.raises(
        DisconnectedMockExecutionRejected,
        match="durable synthetic occurrence reservation failed",
    ):
        restarted.execute(
            call, (grant,), now_ms=101, one_shot=token, occurrence_id=second,
        )

    assert backend.calls == 1
    assert restarted_occurrences.count_synthetic() == 1
    assert [event.outcome for event in audit.events()] == [
        "mock_pre_action", "mock_completed",
    ]


def test_pre_action_audit_failure_blocks_write_mock_after_reservation(tmp_path):
    (
        backend, _, _, audit, occurrences, executor,
        call, grant, audit_path, _,
    ) = _stack(tmp_path, Effect.WRITE)
    token = OneShotAuthorization("synthetic-token-audit-fail", call.request_id, 500)
    audit.append(call, outcome="seed")
    with sqlite3.connect(audit_path) as connection:
        connection.execute("DELETE FROM action_events")

    with pytest.raises(
        DisconnectedMockExecutionRejected,
        match="pre-action audit failed; mock backend was not called",
    ):
        executor.execute(
            call,
            (grant,),
            now_ms=100,
            one_shot=token,
            occurrence_id="occ_" + "d" * 64,
        )

    assert occurrences.count_synthetic() == 1
    assert backend.calls == 0


def test_non_mock_registered_backend_is_rejected_before_permission_or_dispatch(
    tmp_path,
):
    class ExternalLikeBackend:
        def __init__(self):
            self.calls = 0

        def execute(self, call):
            self.calls += 1
            return call.request_id

    backend = ExternalLikeBackend()
    registry = ToolRegistry((
        ToolRegistration(
            "fixture.external-like",
            "fixture.external-like",
            Effect.READ,
            "not-a-mock-backend",
            backend,
        ),
    ))
    gate = PermissionGate()
    audit = SQLiteActionAudit(
        tmp_path / "audit.sqlite3",
        clock_ms=lambda: 100,
    )
    executor = DisconnectedMockExecutor(registry, gate, audit)
    call = ToolCall(
        "fixture.external-like",
        "fixture.external-like",
        "synthetic:private",
    )
    grant = CapabilityGrant("fixture.external-like", "synthetic:private")

    with pytest.raises(
        DisconnectedMockExecutionRejected,
        match="only the exact disconnected MockToolBackend",
    ):
        executor.execute(call, (grant,), now_ms=10)

    assert backend.calls == 0
    assert gate._consumed_tokens == set()
    assert audit.events() == []


def test_shadowed_audit_method_cannot_bypass_pre_action_gate(tmp_path):
    backend, _, _, audit, _, executor, call, grant, _, _ = _stack(
        tmp_path, Effect.READ,
    )
    audit.append = lambda *_args, **_kwargs: None

    with pytest.raises(
        DisconnectedMockExecutionRejected,
        match="ActionAudit method identity changed",
    ):
        executor.execute(call, (grant,), now_ms=10)

    assert backend.calls == 0
