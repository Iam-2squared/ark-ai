"""Run1109: mock executor audit and authorization failure ordering."""

from __future__ import annotations

from pathlib import Path

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


def _components(tmp_path: Path, effect: Effect, *, clock_ms=None, with_occurrences=True):
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
    audit = SQLiteActionAudit(
        tmp_path / "action-audit.sqlite3",
        clock_ms=clock_ms or (lambda: 100),
    )
    occurrences = (
        SyntheticOccurrenceStore(tmp_path / "occurrences.sqlite3")
        if with_occurrences else None
    )
    executor = DisconnectedMockExecutor(registry, gate, audit, occurrences)
    call = ToolCall(
        "fixture.mock",
        "fixture.mock",
        "synthetic:private",
        {"value": "fixture-only"},
    )
    grant = CapabilityGrant("fixture.mock", "synthetic:private")
    return backend, registry, gate, audit, occurrences, executor, call, grant


def test_completion_audit_failure_after_mock_is_not_retried(tmp_path: Path):
    ticks = iter((100,))

    def clock_ms():
        try:
            return next(ticks)
        except StopIteration as exc:
            raise RuntimeError("synthetic clock unavailable") from exc

    backend, _, _, audit, _, executor, call, grant = _components(
        tmp_path, Effect.READ, clock_ms=clock_ms, with_occurrences=False,
    )

    with pytest.raises(
        DisconnectedMockExecutionRejected,
        match="completion audit failed after mock-only execution",
    ):
        executor.execute(call, (grant,), now_ms=10)

    assert backend.calls == 1
    assert [event.outcome for event in audit.events()] == ["mock_pre_action"]


def test_missing_occurrence_store_blocks_write_before_permission_or_audit(
    tmp_path: Path,
):
    backend, _, gate, audit, _, executor, call, grant = _components(
        tmp_path, Effect.WRITE, with_occurrences=False,
    )
    token = OneShotAuthorization("synthetic-no-ledger", call.request_id, 500)

    with pytest.raises(
        DisconnectedMockExecutionRejected,
        match="require a durable local occurrence store",
    ):
        executor.execute(
            call,
            (grant,),
            now_ms=100,
            one_shot=token,
            occurrence_id="occ_" + "a" * 64,
        )

    assert gate._consumed_tokens == set()
    assert audit.events() == []
    assert backend.calls == 0


def test_durable_token_replay_fails_before_actual_gate_consumption_audit_or_mock(
    tmp_path: Path,
):
    backend, registry, gate, audit, occurrences, executor, call, grant = _components(
        tmp_path, Effect.WRITE,
    )
    assert occurrences is not None
    token = OneShotAuthorization("synthetic-reserved-token", call.request_id, 500)
    first_occurrence = "occ_" + "b" * 64
    second_occurrence = "occ_" + "c" * 64

    occurrences.reserve_synthetic(
        registry,
        call,
        token,
        occurrence_id=first_occurrence,
        now_ms=100,
    )
    with pytest.raises(
        DisconnectedMockExecutionRejected,
        match="durable synthetic occurrence reservation failed",
    ):
        executor.execute(
            call,
            (grant,),
            now_ms=101,
            one_shot=token,
            occurrence_id=second_occurrence,
        )

    assert gate._consumed_tokens == set()
    assert occurrences.count_synthetic() == 1
    assert audit.events() == []
    assert backend.calls == 0
