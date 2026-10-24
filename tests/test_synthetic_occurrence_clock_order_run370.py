"""Caller-supplied clock rollback is rejected inside the durable fixture lock."""

import hashlib
from pathlib import Path

import pytest

from ark.agency.contracts import Effect, OneShotAuthorization, ToolCall
from ark.agency.durable_occurrence_review import (
    SyntheticOccurrenceStore,
    SyntheticReplayRejected,
)
from ark.agency.registry import ToolRegistration, ToolRegistry


class NeverExecute:
    def execute(self, call: ToolCall) -> object:
        raise AssertionError("synthetic fixture must never dispatch")


def _reserve(store: SyntheticOccurrenceStore, name: str, at_ms: int) -> None:
    registry = ToolRegistry(
        (ToolRegistration("mock", "fixture", Effect.WRITE, "offline", NeverExecute()),)
    )
    call = ToolCall("mock", "fixture", "test", {"n": 1})
    store.reserve_synthetic(
        registry,
        call,
        OneShotAuthorization("artificial-" + name, call.request_id, 10_000),
        occurrence_id="occ_" + hashlib.sha256(name.encode()).hexdigest(),
        now_ms=at_ms,
    )


def test_restart_clock_rollback_denied_without_reservation(tmp_path: Path):
    path = tmp_path / "synthetic.sqlite"
    original = SyntheticOccurrenceStore(path)
    _reserve(original, "A", 100)
    reopened = SyntheticOccurrenceStore(path)
    with pytest.raises(SyntheticReplayRejected, match="clock regressed"):
        _reserve(reopened, "B", 99)
    assert reopened.count_synthetic() == 1
    _reserve(reopened, "C", 101)
    assert original.count_synthetic() == 2


def test_equal_timestamp_is_not_a_clock_rollback(tmp_path: Path):
    store = SyntheticOccurrenceStore(tmp_path / "synthetic.sqlite")
    _reserve(store, "A", 100)
    _reserve(store, "B", 100)
    assert store.count_synthetic() == 2


@pytest.mark.parametrize("at_ms", [0, 1, 99])
def test_rollback_does_not_consume_new_token(tmp_path: Path, at_ms: int):
    store = SyntheticOccurrenceStore(tmp_path / "synthetic.sqlite")
    _reserve(store, "A", 100)
    with pytest.raises(SyntheticReplayRejected, match="clock regressed"):
        _reserve(store, "B", at_ms)
    _reserve(store, "B", 101)
    assert store.count_synthetic() == 2
