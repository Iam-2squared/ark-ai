"""Synthetic reservations refuse reflected SQLite source substitutions.

All tests use disconnected fixtures: no ToolBackend is ever called and no
persisted reservation conveys human permission or an external WRITE outcome.
"""

import hashlib
from pathlib import Path

import pytest

import ark.agency.durable_occurrence_review as occurrence_module
from ark.agency.contracts import Effect, OneShotAuthorization, ToolCall
from ark.agency.durable_occurrence_review import (
    SyntheticOccurrenceStore,
    SyntheticReplayRejected,
)
from ark.agency.registry import ToolRegistration, ToolRegistry


class NeverExecute:
    def execute(self, call: ToolCall) -> object:
        raise AssertionError("synthetic reservation must not dispatch")


def _identity():
    registry = ToolRegistry(
        (ToolRegistration("fixture", "write", Effect.WRITE, "offline", NeverExecute()),)
    )
    call = ToolCall("fixture", "write", "local", {"n": 1})
    token = OneShotAuthorization("synthetic-token", call.request_id, 10_000)
    occurrence = "occ_" + hashlib.sha256(b"synthetic-occurrence-source").hexdigest()
    return registry, call, token, occurrence


def _reserve(store, registry, call, token, occurrence):
    return store.reserve_synthetic(
        registry, call, token, occurrence_id=occurrence, now_ms=20,
    )


@pytest.mark.parametrize("different_path", [False, True])
def test_registry_callback_cannot_retarget_reservation_source(
    tmp_path: Path, monkeypatch, different_path: bool,
):
    path = tmp_path / "original.sqlite"
    second = tmp_path / "other.sqlite"
    store = SyntheticOccurrenceStore(path)
    registry, call, token, occurrence = _identity()
    bind = registry.bind

    def retarget(request):
        bound = bind(request)
        store._path = second if different_path else Path(str(path))
        return bound

    monkeypatch.setattr(registry, "bind", retarget)
    with pytest.raises(SyntheticReplayRejected, match="source changed"):
        _reserve(store, registry, call, token, occurrence)
    assert SyntheticOccurrenceStore(path).count_synthetic() == 0
    assert not second.exists()


def test_late_registry_callback_retarget_rolls_back_insert(
    tmp_path: Path, monkeypatch,
):
    path = tmp_path / "original.sqlite"
    store = SyntheticOccurrenceStore(path)
    registry, call, token, occurrence = _identity()
    bind = registry.bind
    attempts = 0

    def retarget_on_second_bind(request):
        nonlocal attempts
        attempts += 1
        bound = bind(request)
        if attempts == 2:
            store._path = Path(str(path))
        return bound

    monkeypatch.setattr(registry, "bind", retarget_on_second_bind)
    with pytest.raises(SyntheticReplayRejected, match="source changed"):
        _reserve(store, registry, call, token, occurrence)
    assert attempts == 2
    assert SyntheticOccurrenceStore(path).count_synthetic() == 0


def test_in_transaction_source_retarget_rolls_back_insert(
    tmp_path: Path, monkeypatch,
):
    path = tmp_path / "original.sqlite"
    store = SyntheticOccurrenceStore(path)
    registry, call, token, occurrence = _identity()
    validate = occurrence_module._validate

    def retarget_during_validation(conn):
        validate(conn)
        store._path = Path(str(path))

    monkeypatch.setattr(occurrence_module, "_validate", retarget_during_validation)
    with pytest.raises(SyntheticReplayRejected, match="source changed"):
        _reserve(store, registry, call, token, occurrence)
    assert SyntheticOccurrenceStore(path).count_synthetic() == 0


def test_readonly_count_refuses_source_retarget(
    tmp_path: Path, monkeypatch,
):
    path = tmp_path / "original.sqlite"
    store = SyntheticOccurrenceStore(path)
    validate = occurrence_module._validate

    def retarget_during_validation(conn):
        validate(conn)
        store._path = Path(str(path))

    monkeypatch.setattr(occurrence_module, "_validate", retarget_during_validation)
    with pytest.raises(SyntheticReplayRejected, match="source changed"):
        store.count_synthetic()


def test_bad_source_type_does_not_open_database(tmp_path: Path):
    path = tmp_path / "original.sqlite"
    store = SyntheticOccurrenceStore(path)
    registry, call, token, occurrence = _identity()
    store._path = str(path)
    with pytest.raises(SyntheticReplayRejected, match="must be a Path"):
        _reserve(store, registry, call, token, occurrence)
    with pytest.raises(SyntheticReplayRejected, match="must be a Path"):
        store.count_synthetic()
    assert SyntheticOccurrenceStore(path).count_synthetic() == 0


def test_stable_source_still_reserves_without_dispatch(tmp_path: Path):
    store = SyntheticOccurrenceStore(tmp_path / "original.sqlite")
    registry, call, token, occurrence = _identity()
    receipt = _reserve(store, registry, call, token, occurrence)
    assert receipt.dispatch_authorized is False
    assert receipt.outcome_known is False
    assert receipt.automatic_replay_authorized is False
    assert store.count_synthetic() == 1
