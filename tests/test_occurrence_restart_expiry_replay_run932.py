"""Registry-bound synthetic occurrence recovery: no token revival after restart.

These disposable fixtures cannot authenticate approval, trusted time, or
external exactly-once effects. No backend is ever invoked.
"""

from __future__ import annotations

import hashlib

import pytest

from ark.agency.contracts import Effect, OneShotAuthorization, ToolCall
from ark.agency.durable_occurrence_review import (
    SyntheticOccurrenceStore,
    SyntheticReplayRejected,
)
from ark.agency.registry import ToolRegistration, ToolRegistry


class _NeverDispatch:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, _call: ToolCall) -> object:
        self.calls += 1
        raise AssertionError("a disconnected reservation invoked a live backend")


def _fixture(effect: Effect = Effect.WRITE):
    backend = _NeverDispatch()
    registry = ToolRegistry((
        ToolRegistration("local.reserve", "private.test", effect, "fake-0", backend),
    ))
    call = ToolCall("local.reserve", "private.test", "fixture:private", {"x": 1})
    return backend, registry, call


def _occ(label: str) -> str:
    return "occ_" + hashlib.sha256(label.encode("ascii")).hexdigest()


def _reserve(
    store: SyntheticOccurrenceStore,
    registry: ToolRegistry,
    call: ToolCall,
    name: str,
    *,
    occurrence: str = "initial",
    timestamp: int = 100,
    expiry: int = 1000,
):
    return store.reserve_synthetic(
        registry,
        call,
        OneShotAuthorization(name, call.request_id, expiry),
        occurrence_id=_occ(occurrence),
        now_ms=timestamp,
    )


@pytest.mark.parametrize(
    ("next_expiry", "next_time", "error"),
    (
        (1000, 101, "already reserved"),
        (2000, 101, "already reserved"),
        (1000, 1000, "expired"),
        (2000, 99, "clock regressed"),
    ),
)
def test_restart_never_revives_a_reserved_token(
    tmp_path, next_expiry: int, next_time: int, error: str,
) -> None:
    backend, registry, call = _fixture()
    path = tmp_path / "synthetic-occurrence.sqlite3"
    initial = SyntheticOccurrenceStore(path)
    first = _reserve(initial, registry, call, "once")
    assert first.dispatch_authorized is False
    assert first.outcome_known is False
    assert first.automatic_replay_authorized is False

    cold = SyntheticOccurrenceStore(path)
    with pytest.raises(SyntheticReplayRejected, match=error):
        _reserve(
            cold, registry, call, "once",
            occurrence="different", timestamp=next_time, expiry=next_expiry,
        )
    assert initial.count_synthetic() == cold.count_synthetic() == 1
    assert backend.calls == 0


def test_second_explicit_synthetic_one_shot_can_reserve_same_request(
    tmp_path,
) -> None:
    backend, registry, call = _fixture()
    path = tmp_path / "repeated-request.sqlite3"
    first_store = SyntheticOccurrenceStore(path)
    a = _reserve(first_store, registry, call, "synthetic-a", occurrence="a")
    restarted = SyntheticOccurrenceStore(path)
    b = _reserve(
        restarted, registry, call, "synthetic-b",
        occurrence="b", timestamp=101,
    )
    # Request identity groups equivalent operations but is not an occurrence.
    assert a.request_id == b.request_id == call.request_id
    assert a.registry_revision == b.registry_revision == registry.revision
    assert a.bound_action_id == b.bound_action_id
    assert a.occurrence_id != b.occurrence_id
    assert restarted.count_synthetic() == first_store.count_synthetic() == 2
    assert all(
        permission is False
        for permission in (
            a.dispatch_authorized, a.outcome_known, a.automatic_replay_authorized,
            b.dispatch_authorized, b.outcome_known, b.automatic_replay_authorized,
        )
    )
    assert backend.calls == 0


def test_effect_change_to_read_does_not_turn_reservation_into_read_permission(
    tmp_path,
) -> None:
    backend, writer, call = _fixture()
    store = SyntheticOccurrenceStore(tmp_path / "effect-change.sqlite3")
    first = _reserve(store, writer, call, "old-token")
    readonly = ToolRegistry((
        ToolRegistration("local.reserve", "private.test", Effect.READ, "fake-0", backend),
    ))
    assert writer.revision != readonly.revision
    with pytest.raises(SyntheticReplayRejected, match="WRITE"):
        _reserve(
            SyntheticOccurrenceStore(store._path), readonly, call,
            "new-token", occurrence="new", timestamp=101,
        )
    assert store.count_synthetic() == 1
    assert first.dispatch_authorized is False
    assert backend.calls == 0
