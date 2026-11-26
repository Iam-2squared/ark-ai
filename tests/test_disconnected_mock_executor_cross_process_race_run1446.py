"""Run1446: process-level race for one disconnected mock WRITE occurrence."""

from __future__ import annotations

from multiprocessing import get_context
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

_TOOL = "fixture.mock"
_SCOPE = "synthetic:private"
_PRIVATE = "raw-private-fixture-value-run1446"
_OCCURRENCE = "occ_" + "a" * 64
_TOKEN_ID = "run1446-shared-token"


def _race_worker(
    audit_path: str,
    occurrence_path: str,
    barrier,
    results,
) -> None:
    backend = MockToolBackend()
    registry = ToolRegistry((
        ToolRegistration(
            _TOOL,
            _TOOL,
            Effect.WRITE,
            "ark.mock.fixture.v1",
            backend,
        ),
    ))
    gate = PermissionGate()
    audit = SQLiteActionAudit(Path(audit_path), clock_ms=lambda: 100)
    occurrences = SyntheticOccurrenceStore(Path(occurrence_path))
    executor = DisconnectedMockExecutor(registry, gate, audit, occurrences)
    call = ToolCall(_TOOL, _TOOL, _SCOPE, {"value": _PRIVATE})
    grant = CapabilityGrant(_TOOL, _SCOPE)
    token = OneShotAuthorization(_TOKEN_ID, call.request_id, 500)

    barrier.wait(timeout=60)
    try:
        receipt = executor.execute(
            call,
            (grant,),
            now_ms=100,
            one_shot=token,
            occurrence_id=_OCCURRENCE,
        )
    except DisconnectedMockExecutionRejected as exc:
        results.put((
            "rejected",
            backend.calls,
            token.token_id in gate._consumed_tokens,
            str(exc),
        ))
    else:
        results.put((
            "completed",
            backend.calls,
            token.token_id in gate._consumed_tokens,
            receipt.dispatch_authorized,
            receipt.automatic_replay_authorized,
            receipt.external_effect_proven,
            receipt.exact_once_external_effect_proven,
            receipt.pre_action_event_id,
            receipt.completion_event_id,
        ))


def test_two_process_executors_share_one_write_occurrence_and_audit_pair(
    tmp_path: Path,
) -> None:
    audit_path = tmp_path / "action-audit.sqlite3"
    occurrence_path = tmp_path / "occurrences.sqlite3"
    # Initialize both stores before the race; this test isolates concurrent
    # reservations and audit-before-mock ordering, not first-open bootstrap.
    SQLiteActionAudit(audit_path, clock_ms=lambda: 90)
    SyntheticOccurrenceStore(occurrence_path)

    context = get_context("spawn")
    barrier = context.Barrier(3)
    results = context.Queue()
    processes = [
        context.Process(
            target=_race_worker,
            args=(str(audit_path), str(occurrence_path), barrier, results),
        )
        for _ in range(2)
    ]
    try:
        for process in processes:
            process.start()
        barrier.wait(timeout=60)
        outcomes = [results.get(timeout=90) for _ in processes]
        for process in processes:
            process.join(timeout=60)
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
                pytest.fail("disconnected executor worker did not terminate")
            assert process.exitcode == 0
    finally:
        for process in processes:
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
        results.close()

    completed = [item for item in outcomes if item[0] == "completed"]
    rejected = [item for item in outcomes if item[0] == "rejected"]
    assert len(completed) == len(rejected) == 1

    winner = completed[0]
    assert winner[1:3] == (1, True)
    assert winner[3:7] == (False, False, False, False)
    assert winner[7:9] == (1, 2)

    loser = rejected[0]
    assert loser[1:3] == (0, False)
    assert "durable synthetic occurrence reservation failed" in loser[3]

    cold_audit = SQLiteActionAudit(audit_path, clock_ms=lambda: 101)
    events = cold_audit.events()
    assert [event.event_id for event in events] == [1, 2]
    assert [event.outcome for event in events] == [
        "mock_pre_action",
        "mock_completed",
    ]
    assert [event.occurred_at_ms for event in events] == [100, 100]
    assert len({event.request_id for event in events}) == 1

    cold_occurrences = SyntheticOccurrenceStore(occurrence_path)
    assert cold_occurrences.count_synthetic() == 1

    persisted = b"".join(
        item.read_bytes() for item in tmp_path.iterdir() if item.is_file()
    )
    assert _PRIVATE.encode("utf-8") not in persisted
