"""Spawn-isolated synthetic WRITE reservation collision regression.

Two distinct operating-system processes reconstruct a registry and local gate,
then race the same SQLite ledger. The reservation receipt must remain inert:
this is not a real authorization, audit-before-action or exactly-once effect.
"""

from __future__ import annotations

from multiprocessing import get_context
from pathlib import Path
from queue import Empty

import pytest

from ark.agency.contracts import (
    CapabilityGrant,
    Effect,
    OneShotAuthorization,
    ToolCall,
)
from ark.agency.durable_occurrence_review import (
    SyntheticOccurrenceStore,
    SyntheticReplayRejected,
)
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry


class _DisconnectedBackend:
    def execute(self, call):
        raise AssertionError("real ToolBackend execution is prohibited")


def _fixture():
    registry = ToolRegistry((
        ToolRegistration(
            "fixture.write", "offline.write", Effect.WRITE, "mock-v1",
            _DisconnectedBackend(),
        ),
    ))
    call = ToolCall(
        "fixture.write", "offline.write", "local:private", {"dry_run": True},
    )
    grant = CapabilityGrant("offline.write", "local:private")
    return registry, call, grant


def _compete(path, token_label, occurrence_label, released, results):
    try:
        registry, call, grant = _fixture()
        token = OneShotAuthorization(token_label, call.request_id, 300)
        bound = PermissionGate().authorize_registered(
            registry, call, (grant,), now_ms=100, one_shot=token,
        )
        results.put(("ready", token_label, bound.bound_action_id))
        if not released.wait(30):
            raise RuntimeError("synthetic reservation start timeout")
        try:
            receipt = SyntheticOccurrenceStore(Path(path)).reserve_synthetic(
                registry, call, token,
                occurrence_id=occurrence_label, now_ms=100,
            )
        except SyntheticReplayRejected as exc:
            results.put(("conflict", token_label, str(exc)))
        else:
            assert receipt.dispatch_authorized is False
            assert receipt.outcome_known is False
            assert receipt.automatic_replay_authorized is False
            results.put(("reserved", token_label, receipt.bound_action_id))
    except Exception as exc:
        results.put(("error", token_label, repr(exc)))


@pytest.mark.parametrize("collision", ("token", "occurrence"))
def test_two_spawned_interpreters_cannot_double_reserve(collision, tmp_path):
    path = tmp_path / "spawned-occurrences.sqlite3"
    ledger = SyntheticOccurrenceStore(path)
    start = get_context("spawn")
    released = start.Event()
    results = start.Queue()
    token_ids = (
        ("same-token", "same-token")
        if collision == "token" else ("first-token", "second-token")
    )
    occurrence_ids = (
        ("occ_" + "a" * 64, "occ_" + "b" * 64)
        if collision == "token" else ("occ_" + "c" * 64,) * 2
    )
    children = [
        start.Process(
            target=_compete,
            args=(str(path), token_ids[i], occurrence_ids[i], released, results),
        )
        for i in range(2)
    ]
    try:
        for child in children:
            child.start()
        prepared = [results.get(timeout=35) for _ in children]
        assert all(item[0] == "ready" for item in prepared), prepared
        assert prepared[0][2] == prepared[1][2]
        released.set()
        outcomes = [results.get(timeout=35) for _ in children]
    except Empty as exc:
        pytest.fail(f"spawned occurrence process hung: {exc}")
    finally:
        released.set()
        for child in children:
            child.join(timeout=20)
            if child.is_alive():
                child.terminate()
                child.join(timeout=5)
        results.close()
        results.join_thread()
    assert all(child.exitcode == 0 for child in children)
    assert sorted(item[0] for item in outcomes) == ["conflict", "reserved"], outcomes
    assert "already reserved" in next(
        item[2] for item in outcomes if item[0] == "conflict"
    )
    assert ledger.count_synthetic() == 1
    assert SyntheticOccurrenceStore(path).count_synthetic() == 1
