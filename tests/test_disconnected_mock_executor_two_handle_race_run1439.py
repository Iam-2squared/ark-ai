"""Run1439: concurrent mock executors share one durable WRITE occurrence."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

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


def test_two_executor_handles_race_for_one_durable_write_occurrence(
    tmp_path: Path,
):
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
    gate_a = PermissionGate()
    gate_b = PermissionGate()
    audit = SQLiteActionAudit(
        tmp_path / "action-audit.sqlite3",
        clock_ms=lambda: 100,
    )
    occurrence_path = tmp_path / "occurrences.sqlite3"
    occurrences_a = SyntheticOccurrenceStore(occurrence_path)
    occurrences_b = SyntheticOccurrenceStore(occurrence_path)
    executor_a = DisconnectedMockExecutor(
        registry, gate_a, audit, occurrences_a,
    )
    executor_b = DisconnectedMockExecutor(
        registry, gate_b, audit, occurrences_b,
    )
    call = ToolCall(
        "fixture.mock",
        "fixture.mock",
        "synthetic:private",
        {"value": "fixture-only"},
    )
    grant = CapabilityGrant("fixture.mock", "synthetic:private")
    token = OneShotAuthorization(
        "run1439-shared-token", call.request_id, 500,
    )
    occurrence_id = "occ_" + "a" * 64
    barrier = Barrier(2)

    def contend(executor: DisconnectedMockExecutor):
        barrier.wait(timeout=15)
        try:
            receipt = executor.execute(
                call,
                (grant,),
                now_ms=100,
                one_shot=token,
                occurrence_id=occurrence_id,
            )
            return ("completed", receipt)
        except DisconnectedMockExecutionRejected as exc:
            return ("rejected", str(exc))

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = tuple(pool.map(contend, (executor_a, executor_b)))

    assert sorted(state for state, _ in results) == ["completed", "rejected"]
    rejection = next(value for state, value in results if state == "rejected")
    assert "durable synthetic occurrence reservation failed" in rejection
    receipt = next(value for state, value in results if state == "completed")
    assert receipt.occurrence_id == occurrence_id
    assert receipt.mock_only is True
    assert receipt.dispatch_authorized is False
    assert receipt.external_effect_proven is False
    assert receipt.exact_once_external_effect_proven is False
    assert receipt.automatic_replay_authorized is False

    assert backend.calls == 1
    assert token.token_id in gate_a._consumed_tokens or token.token_id in gate_b._consumed_tokens
    assert sum(
        token.token_id in gate._consumed_tokens for gate in (gate_a, gate_b)
    ) == 1
    assert occurrences_a.count_synthetic() == 1
    assert occurrences_b.count_synthetic() == 1
    assert [event.outcome for event in audit.events()] == [
        "mock_pre_action",
        "mock_completed",
    ]
